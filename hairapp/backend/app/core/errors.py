"""Errores con forma estable.

El backend **no manda texto de UI** (A18): manda `message_key`, y el cliente lo
resuelve con su catálogo i18n. Así el idioma es decisión del dispositivo y no
hay strings de producto repartidos por la API.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """Error de aplicación con clave de mensaje traducible."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message_key: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message_key)
        self.code = code
        self.message_key = message_key
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message_key": self.message_key, "details": self.details}


class NotFound(AppError):
    def __init__(self, resource: str, **details: Any) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            message_key=f"error.not_found.{resource}",
            details=details,
        )


class Unauthorized(AppError):
    def __init__(self, message_key: str = "error.unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            message_key=message_key,
        )


class Forbidden(AppError):
    def __init__(self, message_key: str = "error.forbidden", **details: Any) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="forbidden",
            message_key=message_key,
            details=details,
        )


class Conflict(AppError):
    def __init__(self, message_key: str, **details: Any) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="conflict",
            message_key=message_key,
            details=details,
        )


class ValidationFailed(AppError):
    def __init__(self, message_key: str, **details: Any) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_failed",
            message_key=message_key,
            details=details,
        )


class ConsentRequired(AppError):
    """Falta un consentimiento específico (A22).

    Es un error de primera clase porque el producto lo trata como tal: sin
    consentimiento de procesamiento de fotos, el análisis de imagen no ocurre,
    y el resto de la app sigue funcionando.
    """

    def __init__(self, purpose: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="consent_required",
            message_key="error.consent_required",
            details={"purpose": purpose},
        )


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    # La firma acepta `Exception` porque es lo que Starlette declara; el
    # registro solo lo asocia a `AppError`, así que el estrechamiento es seguro.
    if not isinstance(exc, AppError):
        return await unhandled_error_handler(_request, exc)
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    # Nunca se filtra la excepción original al cliente: podría contener datos
    # de otra persona usuaria.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "internal_error", "message_key": "error.internal", "details": {}},
    )
