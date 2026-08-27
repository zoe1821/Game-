"""Recibos de suscripción — modelo de dominio.

**El fallo que este módulo corrige.** La primera versión de `/billing/activate`
se creía lo que le mandaba el cliente: plan, fecha de fin, todo. Un móvil
modificado podía concederse el plan de pago escribiendo un JSON. No es una
posibilidad teórica: es el primer sitio donde mira cualquiera que quiera
saltarse un muro de pago.

**El principio que se aplica: fallar cerrado.** Si no se puede verificar un
recibo, no se concede el plan. Nunca al revés. Un fallo de red del servidor de
la tienda deja a la persona sin activar y con un mensaje claro, que es
recuperable; conceder plan por defecto ante un fallo no lo es.

Este módulo es Python puro: describe qué es un recibo válido y qué se deduce
de él. Hablar con Apple y Google es trabajo de la capa de servicios.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime

from .entitlements import Plan


class Store(enum.Enum):
    APP_STORE = "app_store"
    PLAY_STORE = "play_store"

    @property
    def label_key(self) -> str:
        return f"store.{self.value}"


class VerificationStatus(enum.Enum):
    VERIFIED = "verified"
    """La tienda confirmó el recibo."""
    INVALID = "invalid"
    """La tienda dice que ese recibo no es válido."""
    EXPIRED = "expired"
    """Válido, pero la suscripción ya venció."""
    UNVERIFIABLE = "unverifiable"
    """No se pudo comprobar: sin credenciales, o la tienda no respondió.
    **No concede nada.** Es el estado que hace que el sistema falle cerrado."""

    @property
    def grants_access(self) -> bool:
        return self is VerificationStatus.VERIFIED

    @property
    def message_key(self) -> str:
        return f"billing.verification.{self.value}"


#: Identificadores de producto que vendemos. Un recibo que traiga cualquier
#: otro se rechaza aunque sea auténtico: podría ser de otra app del mismo
#: desarrollador, o de un producto que ya no ofrecemos.
PRODUCT_TO_PLAN: dict[str, Plan] = {
    "trichon.studio.monthly": Plan.STUDIO,
    "trichon.studio.annual": Plan.STUDIO,
}


@dataclass(frozen=True)
class ReceiptClaim:
    """Lo que el cliente afirma. Nada de esto se cree sin comprobar."""

    store: Store
    product_id: str
    transaction_id: str
    #: Token opaco que la tienda entrega al cliente al comprar. Es lo único que
    #: se manda a verificar; el resto de campos son solo para contrastar.
    token: str


@dataclass(frozen=True)
class VerifiedSubscription:
    """Lo que la tienda confirma. Esto sí se cree."""

    status: VerificationStatus
    plan: Plan | None
    product_id: str | None
    transaction_id: str | None
    expires_at: date | None
    is_trial: bool = False
    in_grace_period: bool = False
    auto_renewing: bool = True
    environment: str | None = None
    """`production` o `sandbox`. Un recibo de sandbox no vale en producción."""
    detail: str | None = None

    @property
    def grants_access(self) -> bool:
        return self.status.grants_access and self.plan is not None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "message_key": self.status.message_key,
            "plan": self.plan.value if self.plan else None,
            "product_id": self.product_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_trial": self.is_trial,
            "in_grace_period": self.in_grace_period,
            "auto_renewing": self.auto_renewing,
            "environment": self.environment,
        }

    @classmethod
    def rejected(
        cls, status: VerificationStatus, *, detail: str | None = None
    ) -> VerifiedSubscription:
        return cls(
            status=status,
            plan=None,
            product_id=None,
            transaction_id=None,
            expires_at=None,
            detail=detail,
        )


def plan_for_product(product_id: str) -> Plan | None:
    return PRODUCT_TO_PLAN.get(product_id)


def interpret(
    *,
    product_id: str,
    transaction_id: str,
    expires_at: datetime,
    now: datetime,
    is_trial: bool = False,
    auto_renewing: bool = True,
    environment: str = "production",
    grace_period_days: int = 16,
) -> VerifiedSubscription:
    """Traduce una respuesta ya autenticada de la tienda a nuestro modelo.

    El periodo de gracia existe porque las tiendas reintentan el cobro durante
    días cuando falla una tarjeta. Cortar el acceso al primer fallo castigaría
    a quien solo tiene la tarjeta caducada.
    """
    plan = plan_for_product(product_id)
    if plan is None:
        return VerifiedSubscription.rejected(
            VerificationStatus.INVALID, detail=f"producto desconocido: {product_id}"
        )

    expired_for = (now - expires_at).days
    if expired_for > grace_period_days:
        return VerifiedSubscription(
            status=VerificationStatus.EXPIRED,
            plan=None,
            product_id=product_id,
            transaction_id=transaction_id,
            expires_at=expires_at.date(),
            environment=environment,
        )

    return VerifiedSubscription(
        status=VerificationStatus.VERIFIED,
        plan=plan,
        product_id=product_id,
        transaction_id=transaction_id,
        expires_at=expires_at.date(),
        is_trial=is_trial,
        in_grace_period=expires_at < now,
        auto_renewing=auto_renewing,
        environment=environment,
    )
