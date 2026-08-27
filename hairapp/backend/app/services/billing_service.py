"""Orquestación de suscripción y cupo."""

from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.errors import Forbidden
from ..db.base import utcnow
from ..domain.billing.entitlements import Decision, Feature, Plan, Subscription, check
from ..models.billing import FeatureUsageRow, SubscriptionRow


def require(session: Session, user_id: str, feature: Feature, *, today: date | None = None) -> Decision:
    """Comprueba el derecho y lanza si no lo hay.

    El error lleva el desglose completo del cupo en `details`, para que la app
    pueda decir "te quedan 0 de 2 este mes" en vez de un "no puedes" seco.
    """
    decision = evaluate(session, user_id, feature, today=today)
    if not decision.allowed:
        details = {k: v for k, v in decision.as_dict().items() if k != "message_key"}
        raise Forbidden(decision.message_key, **details)
    return decision


def _month_bounds(day: date) -> tuple[date, date]:
    last = calendar.monthrange(day.year, day.month)[1]
    return date(day.year, day.month, 1), date(day.year, day.month, last)


def get_subscription(session: Session, user_id: str, *, today: date | None = None) -> Subscription:
    """Suscripción vigente. Sin fila, plan gratuito: nadie se queda fuera."""
    reference = today or date.today()
    row = session.execute(
        select(SubscriptionRow).where(SubscriptionRow.user_id == user_id)
    ).scalar_one_or_none()

    if row is None:
        start, end = _month_bounds(reference)
        return Subscription(Plan.FREE, start, end)

    try:
        plan = Plan(row.plan)
    except ValueError:
        plan = Plan.FREE
    return Subscription(
        plan=plan,
        period_start=row.period_start,
        period_end=row.period_end,
        cancelled_at=row.cancelled_at,
        in_grace_period=row.in_grace_period,
    )


def usage_count(
    session: Session, user_id: str, feature: Feature, *, today: date | None = None
) -> int:
    period_start, _ = _month_bounds(today or date.today())
    row = session.execute(
        select(FeatureUsageRow).where(
            FeatureUsageRow.user_id == user_id,
            FeatureUsageRow.feature == feature.value,
            FeatureUsageRow.period_start == period_start,
        )
    ).scalar_one_or_none()
    return row.count if row else 0


def evaluate(
    session: Session, user_id: str, feature: Feature, *, today: date | None = None
) -> Decision:
    reference = today or date.today()
    subscription = get_subscription(session, user_id, today=reference)
    return check(
        subscription.effective_plan_on(reference),
        feature,
        used_this_period=usage_count(session, user_id, feature, today=reference),
    )


def record_usage(
    session: Session, user_id: str, feature: Feature, *, today: date | None = None
) -> int:
    """Anota un uso. Solo se llama cuando la acción **ya ha tenido éxito**.

    Cobrar cupo por un análisis que falló sería cobrar por nada.
    """
    if feature.is_own_data:
        return 0
    reference = today or date.today()
    period_start, _ = _month_bounds(reference)

    row = session.execute(
        select(FeatureUsageRow).where(
            FeatureUsageRow.user_id == user_id,
            FeatureUsageRow.feature == feature.value,
            FeatureUsageRow.period_start == period_start,
        )
    ).scalar_one_or_none()

    if row is None:
        row = FeatureUsageRow(
            user_id=user_id, feature=feature.value, period_start=period_start, count=0
        )
        session.add(row)
    row.count += 1
    row.last_used_at = utcnow()
    session.add(row)
    return row.count


def entitlement_summary(
    session: Session, user_id: str, *, today: date | None = None
) -> dict[str, object]:
    """Estado completo para la pantalla de plan.

    Muestra el cupo restante de todo, incluido lo ilimitado, para que la
    persona vea qué tiene y no solo qué le falta.
    """
    reference = today or date.today()
    subscription = get_subscription(session, user_id, today=reference)
    plan = subscription.effective_plan_on(reference)
    period_start, period_end = _month_bounds(reference)

    return {
        "plan": plan.value,
        "plan_label_key": plan.label_key,
        "renews": subscription.renews,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "features": [
            evaluate(session, user_id, feature, today=reference).as_dict()
            for feature in Feature
            if not feature.is_own_data
        ],
        "always_included": [
            {"feature": feature.value, "label_key": feature.label_key}
            for feature in Feature
            if feature.is_own_data
        ],
    }
