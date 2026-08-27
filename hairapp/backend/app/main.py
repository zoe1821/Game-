"""Punto de entrada de la API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import api_router
from .core.config import get_settings
from .core.errors import AppError, app_error_handler, unhandled_error_handler
from .services.engine import get_language, get_rule_engine

logger = logging.getLogger("trichon")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()

    # Los packs de reglas se cargan y validan al arrancar: un pack sin etiqueta
    # de evidencia, sin mecanismo o con lenguaje no permitido impide arrancar,
    # en vez de fallar en la primera petición de alguien.
    engine = get_rule_engine()
    language = get_language()
    logger.info(
        "reglas cargadas: %d | términos de lenguaje controlado: %d",
        len(engine.rules),
        len(language.blocked),
    )

    if settings.is_production and settings.uses_insecure_default_secret:
        raise RuntimeError(
            "TRICHON_SECRET_KEY sigue con el valor de desarrollo. No se arranca en producción."
        )

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Trichon API",
        version="0.1.0",
        description=(
            "Análisis capilar por zonas. Aplicación cosmética y educativa: no "
            "diagnostica ni ofrece valoración médica de ningún tipo."
        ),
        lifespan=lifespan,
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "rules_loaded": len(get_rule_engine().rules),
            "environment": settings.environment,
        }

    @app.get("/api/v1/meta/disclaimer", tags=["meta"])
    def disclaimer() -> dict[str, object]:
        """Límite de la app, expuesto como dato y no como texto suelto.

        La app es cosmética y educativa. Ver docs/04-LEGAL-CHECKLIST.md §1.
        """
        return {
            "is_medical_device": False,
            "message_key": "meta.cosmetic_educational_only",
            "referral_block_key": get_language().referral_block_key,
        }

    return app


app = create_app()
