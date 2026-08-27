"""Derechos de uso: qué puede hacer cada persona según su plan.

Implementa docs/02-MONETIZATION.md. Las reglas duras del paywall están aquí
como código, no como buenas intenciones:

  1. **Nunca se bloquean los datos que la persona ya generó.** Si cancela,
     conserva lectura y exportación de todo su histórico. Solo pierde análisis
     *nuevo*. Está en `Feature.is_own_data`, y hay un test que falla si alguien
     marca como premium una función que lea datos propios.
  2. **La explicabilidad nunca es premium.** Cobrar por el "¿por qué esto?"
     sería exactamente el patrón oscuro que este producto existe para evitar.
  3. **Nunca se usa el miedo.** No hay ninguna función cuya carencia se
     comunique como riesgo para el cabello.

El cupo se cuenta por periodo natural de facturación, no por ventana móvil:
"te quedan 2 análisis este mes" se entiende; "te quedan 2 en las últimas 720
horas" no.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


class Plan(enum.Enum):
    FREE = "free"
    STUDIO = "studio"
    """Trichon Estudio: la suscripción de persona usuaria."""
    PRO = "pro"
    """Trichon Pro: cuenta profesional (estilista o salón)."""

    @property
    def label_key(self) -> str:
        return f"plan.{self.value}"

    @property
    def is_paid(self) -> bool:
        return self is not Plan.FREE


class Feature(enum.Enum):
    """Cada función con cupo o restricción de plan."""

    SCAN = "scan"
    SCALP_SCAN = "scalp_scan"
    INGREDIENT_SCAN = "ingredient_scan"
    ASSISTANT_QUERY = "assistant_query"
    ACTIVE_EXPERIMENT = "active_experiment"
    ACTIVE_ROUTINE = "active_routine"
    TWIN_PROJECTION = "twin_projection"
    STYLIST_REPORT = "stylist_report"
    EXTENDED_HISTORY = "extended_history"
    PRODUCT_COMPARISON = "product_comparison"

    # --- Lo que nunca se limita -------------------------------------------
    JOURNAL_ENTRY = "journal_entry"
    INVENTORY_ITEM = "inventory_item"
    EXPLANATION = "explanation"
    EDUCATION = "education"
    ZONE_CORRECTION = "zone_correction"
    DATA_EXPORT = "data_export"

    @property
    def is_own_data(self) -> bool:
        """True si la función solo lee o escribe datos de la propia persona.

        Estas **no pueden** limitarse por plan. Es la regla 1 del paywall.
        """
        return self in _OWN_DATA_FEATURES

    @property
    def label_key(self) -> str:
        return f"feature.{self.value}"


_OWN_DATA_FEATURES = frozenset(
    {
        Feature.JOURNAL_ENTRY,
        Feature.INVENTORY_ITEM,
        Feature.EXPLANATION,
        Feature.EDUCATION,
        Feature.ZONE_CORRECTION,
        Feature.DATA_EXPORT,
    }
)

#: `None` = sin límite. Un número = cupo por periodo de facturación.
#: Lo que vive en el tier gratuito tiene que servir de verdad: si el gratuito
#: no sirve, la promesa educativa del producto es falsa.
_QUOTAS: dict[Plan, dict[Feature, int | None]] = {
    Plan.FREE: {
        Feature.SCAN: 2,
        Feature.SCALP_SCAN: 0,
        Feature.INGREDIENT_SCAN: 10,
        Feature.ASSISTANT_QUERY: 5,
        Feature.ACTIVE_EXPERIMENT: 1,
        Feature.ACTIVE_ROUTINE: 1,
        Feature.TWIN_PROJECTION: 3,
        Feature.STYLIST_REPORT: 0,
        Feature.EXTENDED_HISTORY: 0,
        Feature.PRODUCT_COMPARISON: 3,
    },
    Plan.STUDIO: dict.fromkeys(
        [
            Feature.SCAN,
            Feature.SCALP_SCAN,
            Feature.INGREDIENT_SCAN,
            Feature.ACTIVE_EXPERIMENT,
            Feature.ACTIVE_ROUTINE,
            Feature.TWIN_PROJECTION,
            Feature.STYLIST_REPORT,
            Feature.EXTENDED_HISTORY,
            Feature.PRODUCT_COMPARISON,
        ],
        None,
    )
    # El asistente sí lleva cupo incluso de pago: es el único coste que escala
    # mal (docs/02-MONETIZATION.md §6) y un cupo honesto es mejor que una
    # degradación silenciosa de la calidad.
    | {Feature.ASSISTANT_QUERY: 150},
    Plan.PRO: dict.fromkeys(list(Feature), None) | {Feature.ASSISTANT_QUERY: 400},
}

#: Meses de histórico visible sin suscripción. Pasado ese plazo el dato **no se
#: borra ni se bloquea la exportación**: solo deja de mostrarse en las vistas de
#: comparación y tendencia, que son las caras de calcular.
FREE_HISTORY_MONTHS = 6


class Reason(enum.Enum):
    ALLOWED = "allowed"
    QUOTA_EXHAUSTED = "quota_exhausted"
    NOT_IN_PLAN = "not_in_plan"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: Reason
    feature: Feature
    plan: Plan
    used: int
    limit: int | None
    message_key: str

    @property
    def remaining(self) -> int | None:
        if self.limit is None:
            return None
        return max(0, self.limit - self.used)

    def as_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason": self.reason.value,
            "feature": self.feature.value,
            "plan": self.plan.value,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "message_key": self.message_key,
        }


def quota(plan: Plan, feature: Feature) -> int | None:
    if feature.is_own_data:
        return None
    return _QUOTAS[plan].get(feature, None)


def check(plan: Plan, feature: Feature, *, used_this_period: int = 0) -> Decision:
    """Decide si una acción está permitida.

    Los datos propios se permiten siempre, en cualquier plan y sin contar cupo.
    """
    if feature.is_own_data:
        return Decision(True, Reason.ALLOWED, feature, plan, used_this_period, None, "entitlement.allowed")

    limit = quota(plan, feature)
    if limit is None:
        return Decision(True, Reason.ALLOWED, feature, plan, used_this_period, None, "entitlement.allowed")
    if limit == 0:
        return Decision(
            False, Reason.NOT_IN_PLAN, feature, plan, used_this_period, 0,
            f"entitlement.not_in_plan.{feature.value}",
        )
    if used_this_period >= limit:
        return Decision(
            False, Reason.QUOTA_EXHAUSTED, feature, plan, used_this_period, limit,
            f"entitlement.quota_exhausted.{feature.value}",
        )
    return Decision(True, Reason.ALLOWED, feature, plan, used_this_period, limit, "entitlement.allowed")


@dataclass(frozen=True)
class Subscription:
    """Estado de suscripción de una cuenta."""

    plan: Plan
    period_start: date
    period_end: date
    cancelled_at: date | None = None
    in_grace_period: bool = False
    """Pago fallido pero aún dentro del plazo de reintento de la tienda."""

    def is_active_on(self, day: date) -> bool:
        if self.plan is Plan.FREE:
            return True
        # Cancelar no corta el acceso al momento: se conserva hasta el final del
        # periodo ya pagado. Cortar antes sería quedarse con dinero por un
        # servicio no prestado.
        return self.period_start <= day <= self.period_end or self.in_grace_period

    def effective_plan_on(self, day: date) -> Plan:
        return self.plan if self.is_active_on(day) else Plan.FREE

    @property
    def renews(self) -> bool:
        return self.plan.is_paid and self.cancelled_at is None
