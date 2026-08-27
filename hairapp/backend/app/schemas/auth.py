from __future__ import annotations

from datetime import date

from pydantic import EmailStr, Field, field_validator

from .common import ApiModel


class RegisterIn(ApiModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    birth_date: date
    locale: str = "es"
    accepted_terms: bool
    accepted_privacy: bool

    @field_validator("locale")
    @classmethod
    def _locale(cls, value: str) -> str:
        if value not in {"es", "en"}:
            raise ValueError("locale no soportado")
        return value


class LoginIn(ApiModel):
    email: EmailStr
    password: str


class RefreshIn(ApiModel):
    refresh_token: str


class TokensOut(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ConsentIn(ApiModel):
    purpose: str
    granted: bool


class ConsentOut(ApiModel):
    purpose: str
    granted: bool
    version: int
    granted_at: str | None = None
    revoked_at: str | None = None


class MeOut(ApiModel):
    id: str
    email: str
    locale: str
    depth_level: str
    profile_completeness: float
    consents: list[ConsentOut]
