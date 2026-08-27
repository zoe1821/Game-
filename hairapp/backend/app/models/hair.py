"""Perfil capilar, zonas, historial, scans, objetivos y rutinas."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, IdMixin, TimestampMixin
from ..domain.hair.zones import Zone

#: `JSON` funciona igual en PostgreSQL (donde se materializa como JSONB vía
#: dialecto) y en SQLite, que es lo que usan los tests. Los campos que llevan
#: JSON son observaciones y payloads de análisis, cuya forma evoluciona; el
#: resto del modelo es relacional estricto a propósito.
JsonDict = dict[str, Any]


class HairProfile(Base, IdMixin, TimestampMixin):
    __tablename__ = "hair_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    depth_level: Mapped[str] = mapped_column(String(16), default="basic", nullable=False)
    wash_frequency_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    water_hardness_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    uses_heat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owns_diffuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    protective_style: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    habits: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    """Hábitos de sueño, producto y entorno (A2). JSON porque el cuestionario
    profundo crece por secciones y no queremos una migración por pregunta."""
    onboarding_essential_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completeness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")  # noqa: F821
    zones: Mapped[list[HairZone]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    goals: Mapped[list[Goal]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    scans: Mapped[list[Scan]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    chemical_events: Mapped[list[ChemicalEvent]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class HairZone(Base, IdMixin, TimestampMixin):
    """Una zona del mapa capilar.

    `measurements` guarda un mapa `campo -> {value, confidence, source,
    observed_at}`. Es el `Measured` del dominio serializado: la procedencia
    viaja con el dato, no en una columna aparte que se pueda olvidar.
    """

    __tablename__ = "hair_zones"
    __table_args__ = (UniqueConstraint("profile_id", "zone"),)

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    zone: Mapped[Zone] = mapped_column(Enum(Zone), nullable=False)
    measurements: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    damage_signs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile: Mapped[HairProfile] = relationship(back_populates="zones")
    history: Mapped[list[ZoneMeasurementHistory]] = relationship(
        back_populates="zone_row", cascade="all, delete-orphan"
    )


class ZoneMeasurementHistory(Base, IdMixin, TimestampMixin):
    """Estimaciones anteriores de una zona.

    Se conservan cuando la persona corrige un valor: la corrección manda, pero
    la estimación previa no se borra, porque el propio historial de aciertos y
    fallos del motor es un dato que importa.
    """

    __tablename__ = "zone_measurement_history"

    zone_row_id: Mapped[str] = mapped_column(
        ForeignKey("hair_zones.id", ondelete="CASCADE"), index=True, nullable=False
    )
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[JsonDict] = mapped_column(JSON, nullable=False)
    replaced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    zone_row: Mapped[HairZone] = relationship(back_populates="history")


class ChemicalEvent(Base, IdMixin, TimestampMixin):
    """Historial químico con fecha y zonas afectadas (A2)."""

    __tablename__ = "chemical_events"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    zones: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    details: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)

    profile: Mapped[HairProfile] = relationship(back_populates="chemical_events")


class Goal(Base, IdMixin, TimestampMixin):
    __tablename__ = "goals"
    __table_args__ = (UniqueConstraint("profile_id", "kind"),)

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    profile: Mapped[HairProfile] = relationship(back_populates="goals")


class ScanStatus(enum.Enum):
    DRAFT = "draft"
    ANALYSING = "analysing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Scan(Base, IdMixin, TimestampMixin):
    __tablename__ = "scans"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), default=ScanStatus.DRAFT, nullable=False
    )
    quality_report: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    interpretation: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped[HairProfile] = relationship(back_populates="scans")
    photos: Mapped[list[ScanPhotoRow]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class ScanPhotoRow(Base, IdMixin, TimestampMixin):
    """Una foto del scan.

    La imagen **nunca** vive aquí: `storage_key` apunta a un bucket privado, y
    el borrado de cuenta purga los objetos además de las filas (A22).
    """

    __tablename__ = "scan_photos"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    angle: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    quality: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    face_cropped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """La persona puede recortar el rostro en el dispositivo antes de subir."""

    scan: Mapped[Scan] = relationship(back_populates="photos")


class Routine(Base, IdMixin, TimestampMixin):
    __tablename__ = "routines"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("hair_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(24), default="wash_day", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    """La rutina generada completa, con la explicación de cada paso."""
