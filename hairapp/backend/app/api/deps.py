"""Dependencias compartidas de la API."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.errors import ConsentRequired, NotFound, Unauthorized
from ..core.security import decode_token
from ..db.session import get_db
from ..models.hair import HairProfile
from ..models.user import ConsentPurpose, User

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> User:
    if credentials is None:
        raise Unauthorized("error.missing_token")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("error.token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("error.invalid_token") from exc

    user = session.get(User, payload["sub"])
    if user is None or not user.is_active or user.deleted_at is not None:
        raise Unauthorized("error.account_unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def current_profile(session: DbSession, user: CurrentUser) -> HairProfile:
    profile = session.execute(
        select(HairProfile).where(HairProfile.user_id == user.id)
    ).scalar_one_or_none()
    if profile is None:
        raise NotFound("hair_profile")
    return profile


CurrentProfile = Annotated[HairProfile, Depends(current_profile)]


def require_consent(purpose: ConsentPurpose):
    """Exige un consentimiento concreto para una operación (A22).

    Se aplica solo a lo que de verdad lo necesita: el análisis de imagen exige
    `PHOTO_PROCESSING`, y nada más de la app se bloquea por no darlo.
    """

    def dependency(user: CurrentUser) -> User:
        if not user.has_consent(purpose):
            raise ConsentRequired(purpose.value)
        return user

    return dependency
