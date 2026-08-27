"""Suscripción y consumo de cupo.

Nota deliberada: estas tablas viven **separadas** del catálogo de productos y
del motor de recomendación, y ningún módulo de `domain/products/` las importa.
Es la separación estructural de docs/02-MONETIZATION.md §4: el ranking de
producto no puede leer nada relacionado con ingresos, ni siquiera por accidente.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, IdMixin, TimestampMixin


class SubscriptionRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    plan: Mapped[str] = mapped_column(String(16), default="free", nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    cancelled_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    in_grace_period: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    #: Identificador de la transacción en App Store o Google Play. Es lo único
    #: que guardamos del pago: la app nunca ve ni almacena datos de tarjeta,
    #: porque el cobro lo hace la tienda.
    store: Mapped[str | None] = mapped_column(String(16), nullable=True)
    store_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    #: País de facturación declarado por la tienda. Se usa para el precio y para
    #: saber qué régimen legal aplica (docs/04-LEGAL-CHECKLIST.md §3.5).
    billing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)


class FeatureUsageRow(Base, IdMixin, TimestampMixin):
    """Consumo de una función dentro de un periodo de facturación.

    Se cuenta por periodo natural, no por ventana móvil: "te quedan 2 análisis
    este mes" se entiende, "te quedan 2 en las últimas 720 horas" no.
    """

    __tablename__ = "feature_usage"
    __table_args__ = (UniqueConstraint("user_id", "feature", "period_start"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    feature: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
