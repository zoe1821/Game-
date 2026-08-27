"""Catálogo, inventario, diario y experimentos.

Recordatorio de arquitectura: `Product` **no tiene campos comerciales** y no
puede tenerlos (docs/02-MONETIZATION.md §4). El test
`tests/test_commercial_separation.py` verifica el modelo del dominio; este
modelo de persistencia refleja exactamente esos campos y ninguno más.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, IdMixin, TimestampMixin

JsonDict = dict[str, Any]


class ProductRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "products"

    brand: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    category: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    size_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_minor_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    available_in: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    inci_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    """Atributos derivados del INCI: fijación, peso, proteína, tensioactivo..."""


class InventoryRow(Base, IdMixin, TimestampMixin):
    """Lo que la persona ya tiene. Punto de partida de toda recomendación (A15)."""

    __tablename__ = "inventory_items"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    custom_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    custom_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    custom_inci: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_left_ratio: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    opened_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    pao_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disliked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[ProductRow | None] = relationship()

    @property
    def expires_on(self) -> date | None:
        """Caducidad tras apertura (A15). `None` si falta cualquiera de los dos
        datos: no se estima una fecha inventada."""
        if self.opened_at is None or self.pao_months is None:
            return None
        month = self.opened_at.month - 1 + self.pao_months
        year = self.opened_at.year + month // 12
        month = month % 12 + 1
        day = min(self.opened_at.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)


class SensitivityRow(Base, IdMixin, TimestampMixin):
    """Alergias y sensibilidades **declaradas por la persona** (A15).

    La app las registra y las usa para avisar; nunca las valora ni las estima.
    """

    __tablename__ = "sensitivities"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inci_name: Mapped[str] = mapped_column(String(240), nullable=False)
    reported_reaction: Mapped[str | None] = mapped_column(Text, nullable=True)


class JournalRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "journal_entries"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    entry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    product_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    technique_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    amounts_ml: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    weather: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    ratings: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    """`{"day1": 4, "day2": 3, ...}`."""
    photo_keys: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    experiment_arm_id: Mapped[str | None] = mapped_column(
        ForeignKey("experiment_arms.id", ondelete="SET NULL"), nullable=True
    )


class ExperimentRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "experiments"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    controlled_variables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    target_repetitions_per_arm: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    shared_anonymously: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """B7: compartir el resultado agregado es opt-in por experimento."""

    arms: Mapped[list[ExperimentArmRow]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentArmRow(Base, IdMixin, TimestampMixin):
    __tablename__ = "experiment_arms"
    __table_args__ = (UniqueConstraint("experiment_id", "label_key"),)

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label_key: Mapped[str] = mapped_column(String(120), nullable=False)
    product_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    technique_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    experiment: Mapped[ExperimentRow] = relationship(back_populates="arms")


class TwinSnapshot(Base, IdMixin, TimestampMixin):
    """Estado del digital twin en un momento dado (A24).

    Se guardan instantáneas en vez de mutar un único registro para poder
    mostrar cómo ha cambiado el comportamiento del cabello con el tiempo.
    """

    __tablename__ = "twin_snapshots"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    state: Mapped[JsonDict] = mapped_column(JSON, nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
