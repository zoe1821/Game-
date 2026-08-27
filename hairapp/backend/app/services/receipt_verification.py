"""Verificación de recibos contra App Store y Google Play.

**Regla de esta capa: fallar cerrado.** Si no hay credenciales configuradas, o
la tienda no responde, el resultado es `UNVERIFIABLE` y **no se concede nada**.
Nunca se concede plan por defecto ante un fallo.

Estado real de cada verificador está en `SupportStatus`, y `/billing/status` lo
expone, para que quede visible en vez de descubrirse el día del lanzamiento.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from ..core.config import get_settings
from ..domain.billing.receipts import (
    ReceiptClaim,
    Store,
    VerificationStatus,
    VerifiedSubscription,
    interpret,
)


@dataclass(frozen=True)
class SupportStatus:
    store: Store
    configured: bool
    reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {"store": self.store.value, "configured": self.configured, "reason": self.reason}


class ReceiptVerifier(Protocol):
    store: Store

    def status(self) -> SupportStatus: ...

    def verify(self, claim: ReceiptClaim) -> VerifiedSubscription: ...


_HTTP_TIMEOUT_SECONDS = 10


def _post_json(url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


class AppStoreVerifier:
    """Verificador de App Store.

    Apple firma sus respuestas con JWS (App Store Server API v2). La
    verificación completa requiere validar la cadena de certificados de Apple,
    que necesita la clave privada y el issuer ID de la cuenta de desarrollo.

    Sin esas credenciales **no se finge una verificación**: se devuelve
    `UNVERIFIABLE`, que no concede nada.
    """

    store = Store.APP_STORE

    def status(self) -> SupportStatus:
        settings = get_settings()
        if not settings.app_store_issuer_id or not settings.app_store_private_key:
            return SupportStatus(
                self.store,
                configured=False,
                reason=(
                    "Faltan TRICHON_APP_STORE_ISSUER_ID y TRICHON_APP_STORE_PRIVATE_KEY. "
                    "Sin ellas no se puede verificar ningún recibo de App Store."
                ),
            )
        return SupportStatus(self.store, configured=True)

    def verify(self, claim: ReceiptClaim) -> VerifiedSubscription:
        support = self.status()
        if not support.configured:
            return VerifiedSubscription.rejected(
                VerificationStatus.UNVERIFIABLE, detail=support.reason
            )
        settings = get_settings()
        base = (
            "https://api.storekit.itunes.apple.com"
            if settings.is_production
            else "https://api.storekit-sandbox.itunes.apple.com"
        )
        try:
            payload = _post_json(
                f"{base}/inApps/v1/subscriptions/{claim.transaction_id}",
                {},
                {"Authorization": f"Bearer {settings.app_store_private_key}"},
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            # Un fallo de red no concede plan. Es recuperable: la persona
            # reintenta y la tienda ya tiene su compra registrada.
            return VerifiedSubscription.rejected(
                VerificationStatus.UNVERIFIABLE, detail=f"App Store no respondió: {exc}"
            )
        return _from_apple_payload(payload, claim)


class PlayStoreVerifier:
    """Verificador de Google Play (Android Publisher API v3).

    Requiere una cuenta de servicio con permiso de lectura de compras.
    """

    store = Store.PLAY_STORE

    def status(self) -> SupportStatus:
        settings = get_settings()
        if not settings.play_package_name or not settings.play_service_account_json:
            return SupportStatus(
                self.store,
                configured=False,
                reason=(
                    "Faltan TRICHON_PLAY_PACKAGE_NAME y TRICHON_PLAY_SERVICE_ACCOUNT_JSON. "
                    "Sin ellas no se puede verificar ningún recibo de Google Play."
                ),
            )
        return SupportStatus(self.store, configured=True)

    def verify(self, claim: ReceiptClaim) -> VerifiedSubscription:
        support = self.status()
        if not support.configured:
            return VerifiedSubscription.rejected(
                VerificationStatus.UNVERIFIABLE, detail=support.reason
            )
        settings = get_settings()
        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{settings.play_package_name}/purchases/subscriptionsv2/tokens/{claim.token}"
        )
        try:
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return VerifiedSubscription.rejected(
                VerificationStatus.UNVERIFIABLE, detail=f"Google Play no respondió: {exc}"
            )
        return _from_google_payload(payload, claim)


def _from_apple_payload(payload: dict[str, object], claim: ReceiptClaim) -> VerifiedSubscription:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return VerifiedSubscription.rejected(
            VerificationStatus.INVALID, detail="App Store no reconoce la transacción"
        )
    first = data[0]
    if not isinstance(first, dict):
        return VerifiedSubscription.rejected(VerificationStatus.INVALID)
    expires_ms = first.get("expiresDate")
    if not isinstance(expires_ms, (int, float)):
        return VerifiedSubscription.rejected(VerificationStatus.INVALID)
    return interpret(
        product_id=str(first.get("productId", claim.product_id)),
        transaction_id=str(first.get("originalTransactionId", claim.transaction_id)),
        expires_at=datetime.fromtimestamp(expires_ms / 1000, tz=UTC),
        now=datetime.now(UTC),
        auto_renewing=bool(first.get("autoRenewStatus", 1)),
        environment=str(first.get("environment", "production")).lower(),
    )


def _from_google_payload(payload: dict[str, object], claim: ReceiptClaim) -> VerifiedSubscription:
    items = payload.get("lineItems")
    if not isinstance(items, list) or not items:
        return VerifiedSubscription.rejected(
            VerificationStatus.INVALID, detail="Google Play no reconoce el token"
        )
    first = items[0]
    if not isinstance(first, dict):
        return VerifiedSubscription.rejected(VerificationStatus.INVALID)
    expiry = first.get("expiryTime")
    if not isinstance(expiry, str):
        return VerifiedSubscription.rejected(VerificationStatus.INVALID)
    try:
        expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    except ValueError:
        return VerifiedSubscription.rejected(VerificationStatus.INVALID)
    return interpret(
        product_id=str(first.get("productId", claim.product_id)),
        transaction_id=str(payload.get("latestOrderId", claim.transaction_id)),
        expires_at=expires_at,
        now=datetime.now(UTC),
        auto_renewing=payload.get("subscriptionState") == "SUBSCRIPTION_STATE_ACTIVE",
    )


class UnconfiguredVerifier:
    """Verificador por defecto: no verifica nada y no concede nada.

    Es lo que hace que el sistema sea seguro **por omisión**. Si alguien
    despliega sin configurar las tiendas, nadie consigue plan de pago gratis:
    simplemente no se puede activar, y el mensaje lo dice.
    """

    def __init__(self, store: Store) -> None:
        self.store = store

    def status(self) -> SupportStatus:
        return SupportStatus(
            self.store, configured=False, reason="No hay verificador configurado para esta tienda."
        )

    def verify(self, claim: ReceiptClaim) -> VerifiedSubscription:
        return VerifiedSubscription.rejected(
            VerificationStatus.UNVERIFIABLE,
            detail="No hay verificador configurado para esta tienda.",
        )


_verifiers: dict[Store, ReceiptVerifier] = {}


def get_verifier(store: Store) -> ReceiptVerifier:
    if store not in _verifiers:
        _verifiers[store] = (
            AppStoreVerifier() if store is Store.APP_STORE else PlayStoreVerifier()
        )
    return _verifiers[store]


def set_verifier(store: Store, verifier: ReceiptVerifier) -> None:
    """Punto de inyección para tests. No se usa en producción."""
    _verifiers[store] = verifier


def reset_verifiers() -> None:
    _verifiers.clear()


def support_status() -> list[dict[str, object]]:
    return [get_verifier(store).status().as_dict() for store in Store]
