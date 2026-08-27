"""Configuración de la aplicación."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRICHON_", env_file=".env", extra="ignore")

    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+psycopg://trichon:trichon@localhost:5432/trichon"

    #: Secreto de firma de tokens. En producción **debe** venir del entorno; el
    #: valor por defecto solo sirve para desarrollo local y el arranque avisa.
    secret_key: str = "dev-only-insecure-change-me-not-for-production-use"
    access_token_minutes: int = 30
    refresh_token_days: int = 30

    #: Edad mínima. Decisión de producto documentada en
    #: docs/04-LEGAL-CHECKLIST.md §4: v1 se restringe a mayores de 16.
    minimum_age_years: int = 16

    storage_bucket: str = "trichon-photos"
    storage_endpoint: str | None = None
    presigned_url_seconds: int = 300

    default_locale: str = "es"
    supported_locales: tuple[str, ...] = ("es", "en")

    redis_url: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def uses_insecure_default_secret(self) -> bool:
        return self.secret_key.startswith("dev-only-insecure")


@lru_cache
def get_settings() -> Settings:
    return Settings()
