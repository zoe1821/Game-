"""Hash de contraseñas y tokens.

Argon2id para contraseñas (resistente a GPU y a ASIC, ganador de la Password
Hashing Competition). JWT de acceso corto + refresh rotatorio.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .config import get_settings

_hasher = PasswordHasher()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except (InvalidHashError, ValueError):
        return True


def create_access_token(subject: str, *, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "jti": uuid.uuid4().hex,
    }
    payload.update(extra or {})
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Devuelve `(token, jti)`. El `jti` se guarda para poder revocarlo."""
    settings = get_settings()
    now = datetime.now(UTC)
    jti = uuid.uuid4().hex
    token = jwt.encode(
        {
            "sub": subject,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=settings.refresh_token_days),
            "jti": jti,
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    return token, jti


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"se esperaba un token de tipo {expected_type}")
    return payload


def random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
