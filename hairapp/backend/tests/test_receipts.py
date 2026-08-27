"""Verificación de recibos: el sistema tiene que fallar cerrado.

Es la diferencia entre un muro de pago y un muro de pago que se salta
escribiendo un JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.billing.entitlements import Plan
from app.domain.billing.receipts import (
    ReceiptClaim,
    Store,
    VerificationStatus,
    VerifiedSubscription,
    interpret,
    plan_for_product,
)
from app.services.receipt_verification import (
    AppStoreVerifier,
    PlayStoreVerifier,
    UnconfiguredVerifier,
)

NOW = datetime(2026, 8, 27, tzinfo=UTC)


def _claim(store: Store = Store.APP_STORE) -> ReceiptClaim:
    return ReceiptClaim(store, "trichon.studio.monthly", "tx-1", "token-abcdefgh")


# --- fallar cerrado -------------------------------------------------------


def test_without_credentials_nothing_is_granted() -> None:
    """El caso que importa: si alguien despliega sin configurar las tiendas,
    nadie consigue plan de pago gratis."""
    for verifier in (AppStoreVerifier(), PlayStoreVerifier()):
        assert not verifier.status().configured
        result = verifier.verify(_claim(verifier.store))
        assert result.status is VerificationStatus.UNVERIFIABLE
        assert not result.grants_access
        assert result.plan is None


def test_unconfigured_verifier_explains_why() -> None:
    verifier = UnconfiguredVerifier(Store.PLAY_STORE)
    status = verifier.status()
    assert not status.configured
    assert status.reason


def test_unverifiable_never_grants_access() -> None:
    rejected = VerifiedSubscription.rejected(VerificationStatus.UNVERIFIABLE)
    assert not rejected.grants_access
    assert not VerificationStatus.UNVERIFIABLE.grants_access


@pytest.mark.parametrize(
    "status",
    [VerificationStatus.INVALID, VerificationStatus.EXPIRED, VerificationStatus.UNVERIFIABLE],
)
def test_only_verified_grants_access(status: VerificationStatus) -> None:
    assert not status.grants_access
    assert VerificationStatus.VERIFIED.grants_access


# --- interpretación de una respuesta ya autenticada -----------------------


def test_a_valid_receipt_grants_the_matching_plan() -> None:
    result = interpret(
        product_id="trichon.studio.monthly",
        transaction_id="tx-1",
        expires_at=NOW + timedelta(days=20),
        now=NOW,
    )
    assert result.grants_access
    assert result.plan is Plan.STUDIO
    assert result.expires_at == (NOW + timedelta(days=20)).date()


def test_a_receipt_for_another_product_is_rejected() -> None:
    """Aunque el recibo sea auténtico: podría ser de otra app del mismo
    desarrollador."""
    result = interpret(
        product_id="otra.app.premium",
        transaction_id="tx-1",
        expires_at=NOW + timedelta(days=20),
        now=NOW,
    )
    assert result.status is VerificationStatus.INVALID
    assert not result.grants_access


def test_an_expired_receipt_does_not_grant_access() -> None:
    result = interpret(
        product_id="trichon.studio.monthly",
        transaction_id="tx-1",
        expires_at=NOW - timedelta(days=40),
        now=NOW,
    )
    assert result.status is VerificationStatus.EXPIRED
    assert not result.grants_access


def test_grace_period_keeps_access_while_the_store_retries_payment() -> None:
    """Cortar al primer cobro fallido castigaría a quien solo tiene la tarjeta
    caducada; las tiendas reintentan durante días."""
    result = interpret(
        product_id="trichon.studio.monthly",
        transaction_id="tx-1",
        expires_at=NOW - timedelta(days=3),
        now=NOW,
    )
    assert result.grants_access
    assert result.in_grace_period


def test_only_known_products_map_to_plans() -> None:
    assert plan_for_product("trichon.studio.monthly") is Plan.STUDIO
    assert plan_for_product("trichon.studio.annual") is Plan.STUDIO
    assert plan_for_product("cualquier.otra.cosa") is None


def test_sandbox_environment_is_carried_through() -> None:
    """Se conserva para poder rechazarlo en producción: un recibo de sandbox
    es la vía más simple de conseguir plan gratis si no se comprueba."""
    result = interpret(
        product_id="trichon.studio.monthly",
        transaction_id="tx-1",
        expires_at=NOW + timedelta(days=10),
        now=NOW,
        environment="sandbox",
    )
    assert result.environment == "sandbox"
