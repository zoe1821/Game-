"""Plan, cupo y activación de suscripción."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from ...core.errors import Forbidden, ValidationFailed
from ...db.session import TransactionalRoute
from ...domain.billing.entitlements import Feature, Plan
from ...models.billing import SubscriptionRow
from ...services.billing_service import entitlement_summary, evaluate
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
def activate(
    plan: str,
    store: str,
    store_transaction_id: str,
    period_end: date,
    user: CurrentUser,
    session: DbSession,
    billing_country: str | None = None,
) -> dict[str, object]:
    """Registra una suscripción ya cobrada por la tienda.

    **La app no cobra.** El cobro lo hace App Store o Google Play y aquí solo
    se guarda el resultado, así que nunca vemos ni almacenamos datos de tarjeta.

    Pendiente antes de producción: verificar el recibo contra el servidor de la
    tienda. Tal como está, este endpoint confía en lo que le manda el cliente,
    lo que basta para desarrollo pero **no** para producción — un cliente
    modificado podría concederse Estudio. Está anotado en el roadmap y en
    docs/02-MONETIZATION.md.
    """
    try:
        parsed = Plan(plan)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_plan", plan=plan) from exc
    if store not in {"app_store", "play_store"}:
        raise ValidationFailed("error.unknown_store", store=store)
    if parsed is Plan.PRO:
        raise Forbidden("error.pro_plan_not_self_serve")

    row = session.execute(
        SubscriptionRow.__table__.select().where(SubscriptionRow.user_id == user.id)
    ).first()

    existing = session.get(SubscriptionRow, row.id) if row else None
    if existing is None:
        existing = SubscriptionRow(user_id=user.id, period_start=date.today(), period_end=period_end)
        session.add(existing)

    existing.plan = parsed.value
    existing.period_start = date.today()
    existing.period_end = period_end
    existing.cancelled_at = None
    existing.in_grace_period = False
    existing.store = store
    existing.store_transaction_id = store_transaction_id
    existing.billing_country = billing_country
    session.flush()

    return entitlement_summary(session, user.id)


@router.post("/cancel")
def cancel(user: CurrentUser, session: DbSession) -> dict[str, object]:
    """Cancela la renovación.

    No corta el acceso al momento: se conserva hasta el final del periodo ya
    pagado. Cortar antes sería quedarse con dinero por un servicio no prestado.
    Y los datos ya generados siguen siendo accesibles siempre, en cualquier plan.
    """
    subscription = session.execute(
        SubscriptionRow.__table__.select().where(SubscriptionRow.user_id == user.id)
    ).first()
    if subscription is not None:
        row = session.get(SubscriptionRow, subscription.id)
        if row is not None:
            row.cancelled_at = date.today()
            session.add(row)
            session.flush()
    return entitlement_summary(session, user.id)


@router.get("/plans")
def plans() -> list[dict[str, object]]:
    """Los planes y qué incluye cada uno, para la pantalla de suscripción."""
    from ...domain.billing.entitlements import quota

    return [
        {
            "plan": plan.value,
            "label_key": plan.label_key,
            "is_paid": plan.is_paid,
            "self_serve": plan is not Plan.PRO,
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
