"""Cuenta, consentimientos y sesiones."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, IdMixin, TimestampMixin


class ConsentPurpose(enum.Enum):
    """Un consentimiento por propósito, separados de verdad (A22, B6 §3.2).

    Que `MODEL_TRAINING` sea independiente y esté desactivado por defecto es un
    requisito, no una preferencia: rechazarlo no degrada ninguna función.
    """

    TERMS = "terms"
    PRIVACY = "privacy"
    PHOTO_PROCESSING = "photo_processing"
    MODEL_TRAINING = "model_training"
    STYLIST_SHARING = "stylist_sharing"
    ANONYMOUS_AGGREGATE = "anonymous_aggregate"

    @property
    def is_required_to_use_the_app(self) -> bool:
        return self in {ConsentPurpose.TERMS, ConsentPurpose.PRIVACY}


class DepthLevel(enum.Enum):
    """Nivel de profundidad elegido por la persona (B3).

    Las funciones avanzadas están ocultas por defecto: se activan aquí, no se
    imponen.
    """

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    """Fecha, no un checkbox de «soy mayor de edad» (B6 §4)."""
    locale: Mapped[str] = mapped_column(String(8), default="es", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    consents: Mapped[list[Consent]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped[HairProfile | None] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def has_consent(self, purpose: ConsentPurpose) -> bool:
        for consent in self.consents:
            if consent.purpose is purpose and consent.granted and consent.revoked_at is None:
                return True
        return False


class Consent(Base, IdMixin, TimestampMixin):
    __tablename__ = "consents"
    __table_args__ = (UniqueConstraint("user_id", "purpose", "version"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(Enum(ConsentPurpose), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="consents")


class RefreshToken(Base, IdMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
