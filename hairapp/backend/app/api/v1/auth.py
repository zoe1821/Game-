"""Registro, sesión y consentimientos."""

from __future__ import annotations

from datetime import date, timedelta

import jwt
from fastapi import APIRouter, status
from sqlalchemy import select

from ...core.config import get_settings
from ...core.errors import Conflict, Unauthorized, ValidationFailed
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ...db.base import utcnow
from ...db.session import TransactionalRoute
from ...models.hair import HairProfile
from ...models.user import Consent, ConsentPurpose, RefreshToken, User
from ...schemas.auth import (
    ConsentIn,
    ConsentOut,
    LoginIn,
    MeOut,
    RefreshIn,
    RegisterIn,
    TokensOut,
)
from ...services.profile_service import ensure_zones
from ..deps import CurrentUser, DbSession

router = APIRouter(prefix="/auth", tags=["auth"], route_class=TransactionalRoute)


def _age_years(birth_date: date, *, today: date | None = None) -> int:
    reference = today or date.today()
    years = reference.year - birth_date.year
    if (reference.month, reference.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _issue_tokens(session: DbSession, user: User) -> TokensOut:
    settings = get_settings()
    access = create_access_token(user.id, extra={"locale": user.locale})
    refresh, jti = create_refresh_token(user.id)
    session.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    return TokensOut(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=TokensOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, session: DbSession) -> TokensOut:
    settings = get_settings()

    # Puerta de edad real, no un checkbox (docs/04-LEGAL-CHECKLIST.md §4).
    if _age_years(payload.birth_date) < settings.minimum_age_years:
        raise ValidationFailed(
            "error.minimum_age", minimum_age=settings.minimum_age_years
        )
    if not (payload.accepted_terms and payload.accepted_privacy):
        raise ValidationFailed("error.terms_and_privacy_required")

    existing = session.execute(
        select(User).where(User.email == payload.email.lower())
    ).scalar_one_or_none()
    if existing is not None:
        raise Conflict("error.email_taken")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        birth_date=payload.birth_date,
        locale=payload.locale,
    )
    session.add(user)
    session.flush()

    now = utcnow()
    for purpose in (ConsentPurpose.TERMS, ConsentPurpose.PRIVACY):
        session.add(
            Consent(user_id=user.id, purpose=purpose, granted=True, version=1, granted_at=now)
        )
    # Los demás consentimientos NO se crean concedidos. En particular
    # MODEL_TRAINING queda sin conceder por defecto y rechazarlo no degrada nada.

    profile = HairProfile(user_id=user.id)
    session.add(profile)
    session.flush()
    ensure_zones(session, profile)

    return _issue_tokens(session, user)


@router.post("/login", response_model=TokensOut)
def login(payload: LoginIn, session: DbSession) -> TokensOut:
    user = session.execute(
        select(User).where(User.email == payload.email.lower())
    ).scalar_one_or_none()
    # Se verifica siempre, exista o no la cuenta, para no filtrar por tiempo de
    # respuesta qué correos están registrados.
    password_hash = user.password_hash if user else hash_password("placeholder")
    valid = verify_password(payload.password, password_hash)

    if user is None or not valid or not user.is_active or user.deleted_at is not None:
        raise Unauthorized("error.invalid_credentials")
    return _issue_tokens(session, user)


@router.post("/refresh", response_model=TokensOut)
def refresh(payload: RefreshIn, session: DbSession) -> TokensOut:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("error.invalid_token") from exc

    stored = session.execute(
        select(RefreshToken).where(RefreshToken.jti == claims["jti"])
    ).scalar_one_or_none()
    if stored is None or not stored.is_active:
        raise Unauthorized("error.token_revoked")

    user = session.get(User, claims["sub"])
    if user is None or not user.is_active or user.deleted_at is not None:
        raise Unauthorized("error.account_unavailable")

    # Rotación: el refresh usado se revoca al emitir el siguiente.
    stored.revoked_at = utcnow()
    session.add(stored)
    return _issue_tokens(session, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, session: DbSession) -> None:
    now = utcnow()
    for token in user.refresh_tokens:
        if token.is_active:
            token.revoked_at = now
            session.add(token)


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser, session: DbSession) -> MeOut:
    profile = session.execute(
        select(HairProfile).where(HairProfile.user_id == user.id)
    ).scalar_one_or_none()
    return MeOut(
        id=user.id,
        email=user.email,
        locale=user.locale,
        depth_level=profile.depth_level if profile else "basic",
        profile_completeness=profile.completeness if profile else 0.0,
        consents=[_consent_out(c) for c in user.consents],
    )


@router.put("/consents", response_model=list[ConsentOut])
def update_consents(
    payload: list[ConsentIn], user: CurrentUser, session: DbSession
) -> list[ConsentOut]:
    """Concede o revoca consentimientos. Revocar es tan fácil como conceder."""
    now = utcnow()
    by_purpose = {c.purpose: c for c in user.consents}

    for item in payload:
        try:
            purpose = ConsentPurpose(item.purpose)
        except ValueError as exc:
            raise ValidationFailed("error.unknown_consent_purpose", purpose=item.purpose) from exc

        if purpose.is_required_to_use_the_app and not item.granted:
            raise ValidationFailed("error.cannot_revoke_required_consent", purpose=purpose.value)

        consent = by_purpose.get(purpose)
        if consent is None:
            consent = Consent(user_id=user.id, purpose=purpose, version=1)
            session.add(consent)
            user.consents.append(consent)

        consent.granted = item.granted
        consent.granted_at = now if item.granted else consent.granted_at
        consent.revoked_at = None if item.granted else now

    session.flush()
    return [_consent_out(c) for c in user.consents]


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user: CurrentUser, session: DbSession) -> None:
    """Borrado real de cuenta (A22).

    Elimina las filas en cascada. La purga de los objetos de storage la
    encadena el servicio de almacenamiento a partir de las `storage_key` de las
    fotos: borrar solo las filas dejaría las imágenes en el bucket, que es
    exactamente lo que el compromiso de privacidad prohíbe.
    """
    from ...services.storage import purge_user_objects

    purge_user_objects(session, user)
    session.delete(user)


def _consent_out(consent: Consent) -> ConsentOut:
    return ConsentOut(
        purpose=consent.purpose.value,
        granted=consent.granted,
        version=consent.version,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        revoked_at=consent.revoked_at.isoformat() if consent.revoked_at else None,
    )
