from __future__ import annotations

import pytest

from app.domain.evidence.language import ControlledLanguage
from app.domain.rules.engine import RuleEngine
from app.domain.rules.loader import load_all


@pytest.fixture(scope="session")
def language() -> ControlledLanguage:
    return ControlledLanguage.load()


@pytest.fixture(scope="session")
def rules(language: ControlledLanguage):
    return load_all(language=language)


@pytest.fixture(scope="session")
def engine(rules) -> RuleEngine:
    return RuleEngine(rules)


@pytest.fixture()
def verified_store():
    """Sustituye los verificadores por uno que sí verifica.

    Existe porque los reales, sin credenciales, rechazan todo — que es
    justamente el comportamiento correcto y lo que cubre
    `test_activation_without_a_configured_store_grants_nothing`.
    """
    from datetime import UTC, datetime, timedelta

    from app.domain.billing.receipts import (
        ReceiptClaim,
        Store,
        VerificationStatus,
        VerifiedSubscription,
        interpret,
    )
    from app.services.receipt_verification import SupportStatus, reset_verifiers, set_verifier

    class _FakeVerifier:
        def __init__(self, store: Store) -> None:
            self.store = store

        def status(self) -> SupportStatus:
            return SupportStatus(self.store, configured=True)

        def verify(self, claim: ReceiptClaim) -> VerifiedSubscription:
            if not claim.token.startswith("token-"):
                return VerifiedSubscription.rejected(VerificationStatus.INVALID)
            now = datetime.now(UTC)
            return interpret(
                product_id=claim.product_id,
                # El id de transacción sale del "recibo", no de lo que dijo el
                # cliente: así dos cuentas con el mismo token colisionan.
                transaction_id=claim.token,
                expires_at=now + timedelta(days=30),
                now=now,
            )

    for store in Store:
        set_verifier(store, _FakeVerifier(store))
    yield
    reset_verifiers()
