"""Plan, cupo y activación de suscripción."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from sqlalchemy import select

from ...core.config import get_settings
from ...core.errors import Forbidden, ValidationFailed
from ...db.session import TransactionalRoute
from ...domain.billing.entitlements import Feature, Plan
from ...domain.billing.pricing import catalogue, price_for, tier_for
from ...domain.billing.receipts import ReceiptClaim, Store
from ...models.billing import SubscriptionRow
from ...schemas.billing import ActivateIn
from ...services.billing_service import entitlement_summary, evaluate
from ...services.receipt_verification import get_verifier, support_status
from ..deps import CurrentUser, DbSession

router = APIRouter(prefix="/billing", tags=["billing"], route_class=TransactionalRoute)


@router.get("/entitlements")
def entitlements(user: CurrentUser, session: DbSession) -> dict[str, object]:
    """Qué incluye tu plan y cuánto cupo te queda.

    Incluye a propósito la lista de lo que nunca se limita: es la forma de
    dejar visible que tus propios datos no están detrás del muro.
    """
    return entitlement_summary(session, user.id)


@router.get("/check")
def check_feature(feature: str, user: CurrentUser, session: DbSession) -> dict[str, object]:
    try:
        parsed = Feature(feature)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_feature", feature=feature) from exc
    return evaluate(session, user.id, parsed).as_dict()


@router.post("/activate")
def activate(payload: ActivateIn, user: CurrentUser, session: DbSession) -> dict[str, object]:
    """Activa una suscripción **tras verificar el recibo contra la tienda**.

    Nada de lo que manda el cliente se cree: ni el plan, ni la fecha de fin, ni
    el precio. Solo se manda el token a la tienda y se usa lo que la tienda
    responda. El cliente podría mentir en todo lo demás; el token no puede
    falsificarlo.

    Si el recibo no se puede verificar — sin credenciales configuradas, o la
    tienda no responde — **no se concede nada**. Fallar cerrado es la única
    postura correcta aquí: un fallo de red que deja a alguien sin activar es
    recuperable; conceder plan de pago a quien no pagó, no.
    """
    try:
        store = Store(payload.store)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_store", store=payload.store) from exc

    verified = get_verifier(store).verify(
        ReceiptClaim(
            store=store,
            product_id=payload.product_id,
            transaction_id=payload.transaction_id,
            token=payload.token,
        )
    )

    if not verified.grants_access:
        raise Forbidden(
            verified.status.message_key,
            status=verified.status.value,
            store=store.value,
            detail=verified.detail,
        )

    # Un recibo de sandbox no vale en producción: es la vía más simple de
    # conseguir plan de pago gratis si no se comprueba.
    if get_settings().is_production and verified.environment == "sandbox":
        raise Forbidden("billing.verification.sandbox_receipt_in_production")

    # Un mismo recibo no puede activar dos cuentas distintas.
    clash = session.execute(
        select(SubscriptionRow).where(
            SubscriptionRow.store_transaction_id == verified.transaction_id,
            SubscriptionRow.user_id != user.id,
        )
    ).scalar_one_or_none()
    if clash is not None:
        raise Forbidden("billing.verification.receipt_already_used")

    row = session.execute(
        select(SubscriptionRow).where(SubscriptionRow.user_id == user.id)
    ).scalar_one_or_none()
    if row is None:
        row = SubscriptionRow(user_id=user.id, period_start=date.today(), period_end=date.today())
        session.add(row)

    assert verified.plan is not None and verified.expires_at is not None
    row.plan = verified.plan.value
    row.period_start = date.today()
    row.period_end = verified.expires_at
    row.cancelled_at = None if verified.auto_renewing else date.today()
    row.in_grace_period = verified.in_grace_period
    row.store = store.value
    row.store_transaction_id = verified.transaction_id
    row.billing_country = payload.billing_country
    session.flush()

    return {**entitlement_summary(session, user.id), "verification": verified.as_dict()}


@router.get("/verification-status")
def verification_status() -> dict[str, object]:
    """Si la verificación de recibos está configurada, y por qué no si no lo está.

    Se expone a propósito: que falte configurar una tienda tiene que ser
    visible antes del lanzamiento, no descubrirse cuando alguien intente pagar.
    """
    return {
        "stores": support_status(),
        "billing_configured": get_settings().billing_is_configured,
    }


@router.post("/cancel")
def cancel(user: CurrentUser, session: DbSession) -> dict[str, object]:
    """Cancela la renovación.

    No corta el acceso al momento: se conserva hasta el final del periodo ya
    pagado. Cortar antes sería quedarse con dinero por un servicio no prestado.
    Y los datos ya generados siguen siendo accesibles siempre, en cualquier plan.
    """
    row = session.execute(
        select(SubscriptionRow).where(SubscriptionRow.user_id == user.id)
    ).scalar_one_or_none()
    if row is not None:
        row.cancelled_at = date.today()
        session.add(row)
        session.flush()
    return entitlement_summary(session, user.id)


@router.get("/pricing")
def pricing(country: str | None = None) -> dict[str, object]:
    """Precio del plan en el país indicado.

    Existe porque aplicar un precio en dólares tal cual a toda LATAM deja el
    producto fuera de alcance en la mayoría de sus mercados. Sin país, se usa
    el nivel intermedio, que es el que cubre México y Brasil.
    """
    price = price_for(Plan.STUDIO, country)
    return {
        "country": country.upper() if country else None,
        "tier": tier_for(country).value,
        "studio": price.as_dict() if price else None,
    }


@router.get("/pricing/catalogue")
def pricing_catalogue() -> list[dict[str, object]]:
    """La escala completa, para poder revisarla de un vistazo."""
    return catalogue()


@router.get("/plans")
def plans(country: str | None = None) -> list[dict[str, object]]:
    """Los planes y qué incluye cada uno, para la pantalla de suscripción."""
    from ...domain.billing.entitlements import quota

    return [
        {
            "plan": plan.value,
            "label_key": plan.label_key,
            "is_paid": plan.is_paid,
            "self_serve": plan is not Plan.PRO,
            "price": (lambda p: p.as_dict() if p else None)(price_for(plan, country)),
            "features": [
                {
                    "feature": feature.value,
                    "label_key": feature.label_key,
                    "limit": quota(plan, feature),
                    "always_included": feature.is_own_data,
                }
                for feature in Feature
            ],
        }
        for plan in Plan
    ]
