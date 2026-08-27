"""Tests de integración de la API sobre SQLite en memoria de disco temporal."""

from __future__ import annotations

import io
from datetime import date, timedelta

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TRICHON_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("TRICHON_SECRET_KEY", "test-secret-key-long-enough-for-hmac-sha256")
    monkeypatch.setenv("TRICHON_ENVIRONMENT", "test")

    from app.core.config import get_settings
    from app.db import base as db_base
    from app.services import storage as storage_module

    get_settings.cache_clear()
    db_base._engine = None
    db_base._SessionLocal = None
    storage_module.set_storage(storage_module.LocalStorage(tmp_path / "storage"))

    import app.models  # noqa: F401
    from app.main import create_app

    db_base.Base.metadata.create_all(db_base.get_engine())
    with TestClient(create_app()) as test_client:
        yield test_client

    db_base._engine = None
    db_base._SessionLocal = None
    get_settings.cache_clear()


def _register(client, *, email="a@example.com", born_years_ago=30):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "una-contrasena-larga-y-buena",
            "birth_date": (date.today() - timedelta(days=365 * born_years_ago)).isoformat(),
            "locale": "es",
            "accepted_terms": True,
            "accepted_privacy": True,
        },
    )


def _auth(client, **kwargs) -> dict[str, str]:
    response = _register(client, **kwargs)
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _photo_bytes(size: int = 900, seed: int = 3) -> bytes:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    strands = 40 * np.sin(x * 1.7 + 8 * np.sin(y / 40.0)) + 18 * rng.standard_normal((size, size))
    base = np.clip(120 + 35 * np.sin(y / 120.0) + strands, 0, 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(np.stack([base] * 3, -1)).save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


# --- salud y metadatos ----------------------------------------------------


def test_health_reports_loaded_rules(client) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["rules_loaded"] > 20


def test_disclaimer_states_it_is_not_a_medical_device(client) -> None:
    body = client.get("/api/v1/meta/disclaimer").json()
    assert body["is_medical_device"] is False
    assert body["referral_block_key"]


# --- registro y consentimientos ------------------------------------------


def test_registration_creates_the_full_zone_map(client) -> None:
    headers = _auth(client)
    zones = client.get("/api/v1/profile/zones", headers=headers).json()
    assert len(zones) == 15
    assert all(z["measurements"] == {} for z in zones)


def test_age_gate_is_a_real_date_check(client) -> None:
    """B6 §4: v1 se restringe a mayores de 16."""
    response = _register(client, email="joven@example.com", born_years_ago=14)
    assert response.status_code == 422
    assert response.json()["message_key"] == "error.minimum_age"


def test_model_training_consent_is_off_by_default(client) -> None:
    """A22: rechazarlo es el estado por defecto y no degrada nada."""
    headers = _auth(client)
    me = client.get("/api/v1/auth/me", headers=headers).json()
    granted = {c["purpose"] for c in me["consents"] if c["granted"]}
    assert granted == {"terms", "privacy"}
    assert "model_training" not in granted


def test_required_consents_cannot_be_revoked_while_using_the_app(client) -> None:
    headers = _auth(client)
    response = client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "privacy", "granted": False}],
    )
    assert response.status_code == 422
    assert response.json()["message_key"] == "error.cannot_revoke_required_consent"


def test_consent_can_be_granted_and_revoked_freely(client) -> None:
    headers = _auth(client)
    for granted in (True, False):
        response = client.put(
            "/api/v1/auth/consents",
            headers=headers,
            json=[{"purpose": "model_training", "granted": granted}],
        )
        assert response.status_code == 200
        state = {c["purpose"]: c["granted"] for c in response.json()}
        assert state["model_training"] is granted


def test_duplicate_email_is_rejected(client) -> None:
    _auth(client)
    assert _register(client).status_code == 409


def test_login_does_not_leak_whether_an_email_exists(client) -> None:
    _auth(client)
    unknown = client.post(
        "/api/v1/auth/login", json={"email": "nope@example.com", "password": "x" * 12}
    )
    wrong = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "x" * 12}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_refresh_token_rotates_and_the_old_one_stops_working(client) -> None:
    tokens = _register(client).json()
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert replay.status_code == 401
    assert replay.json()["message_key"] == "error.token_revoked"


def test_protected_endpoints_require_a_token(client) -> None:
    assert client.get("/api/v1/profile").status_code == 401


# --- onboarding (B3) ------------------------------------------------------


def test_essential_onboarding_is_short_and_stores_low_confidence_estimates(client) -> None:
    headers = _auth(client)
    response = client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={
            "dominant_pattern": "3b",
            "approximate_length_cm": 32,
            "wash_frequency_days": 4,
            "primary_goal": "definition",
            "country": "ES",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["onboarding_essential_done"]
    assert body["goals"] == ["definition"]

    crown = next(z for z in body["zones"] if z["zone"] == "crown")
    pattern = crown["measurements"]["pattern"]
    assert pattern["value"] == "3b"
    assert pattern["source"] == "inferred"
    # Una respuesta rápida no es un análisis: la confianza lo refleja.
    assert pattern["confidence"] < 0.6


def test_deep_onboarding_is_optional_and_raises_completeness(client) -> None:
    headers = _auth(client)
    client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={"primary_goal": "definition"},
    )
    before = client.get("/api/v1/profile", headers=headers).json()["completeness"]
    after = client.post(
        "/api/v1/profile/onboarding/deep",
        headers=headers,
        json={"section": "environment", "answers": {"water_hardness_ppm": 240}},
    ).json()
    assert after["completeness"] > before
    assert after["water_hardness_ppm"] == 240


def test_advanced_techniques_are_hidden_at_basic_depth(client) -> None:
    """B3: las funciones avanzadas están ocultas hasta que se activan."""
    headers = _auth(client)
    basic = client.get("/api/v1/routines/techniques", headers=headers).json()
    assert all(t["difficulty"] != "advanced" for t in basic)

    client.put("/api/v1/profile/depth-level", headers=headers, params={"level": "advanced"})
    advanced = client.get("/api/v1/routines/techniques", headers=headers).json()
    assert any(t["difficulty"] == "advanced" for t in advanced)


# --- corrección manual (A1.4) --------------------------------------------


def test_manual_correction_is_final(client) -> None:
    headers = _auth(client)
    client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={"dominant_pattern": "3b", "primary_goal": "definition"},
    )
    corrected = client.put(
        "/api/v1/profile/zones/crown",
        headers=headers,
        json={"field": "pattern", "value": "4a"},
    ).json()
    assert corrected["measurements"]["pattern"]["value"] == "4a"
    assert corrected["measurements"]["pattern"]["source"] == "user"
    assert corrected["measurements"]["pattern"]["confidence"] == 1.0

    # Un onboarding posterior no puede pisarla.
    client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={"dominant_pattern": "2a", "primary_goal": "definition"},
    )
    after = client.get("/api/v1/profile/zones", headers=headers).json()
    crown = next(z for z in after if z["zone"] == "crown")
    assert crown["measurements"]["pattern"]["value"] == "4a"

    # Y una zona que no se corrigió sí acepta la nueva estimación.
    nape = next(z for z in after if z["zone"] == "nape")
    assert nape["measurements"]["pattern"]["value"] == "2a"


def test_non_measurable_fields_are_rejected(client) -> None:
    headers = _auth(client)
    response = client.put(
        "/api/v1/profile/zones/crown",
        headers=headers,
        json={"field": "favourite_colour", "value": "azul"},
    )
    assert response.status_code == 422


# --- rutinas --------------------------------------------------------------


def test_generated_routine_explains_every_step(client) -> None:
    headers = _auth(client)
    client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={"dominant_pattern": "3b", "approximate_length_cm": 30, "primary_goal": "definition"},
    )
    routine = client.post(
        "/api/v1/routines/generate",
        headers=headers,
        json={"kind": "wash_day", "temperature_c": 24, "relative_humidity": 70},
    ).json()

    assert routine["steps"]
    for step in routine["steps"]:
        explanation = step["explanation"]
        assert explanation["summary_key"]
        assert explanation["evidence_level"]
        assert "sample_size" in explanation
        # Sin historial, la confianza personal es 0 y se declara el arranque en frío.
        assert explanation["personal_confidence"] == 0.0


def test_referral_signs_stop_the_routine_entirely(client) -> None:
    """A23: ante señales que exigen evaluación profesional, no se estima nada."""
    headers = _auth(client)
    client.post(
        "/api/v1/profile/onboarding/essential",
        headers=headers,
        json={"dominant_pattern": "3b", "primary_goal": "definition"},
    )
    routine = client.post(
        "/api/v1/routines/generate",
        headers=headers,
        json={"kind": "wash_day", "scalp_referral_signs": ["open_wound"]},
    ).json()
    assert routine["halted"] is True
    assert routine["steps"] == []
    assert routine["halt_block_key"] == "safety.referral_block"


def test_weather_forecast_uses_dew_point(client) -> None:
    headers = _auth(client)
    cold = client.get(
        "/api/v1/routines/weather-forecast",
        headers=headers,
        params={"temperature_c": 5, "relative_humidity": 80},
    ).json()
    warm = client.get(
        "/api/v1/routines/weather-forecast",
        headers=headers,
        params={"temperature_c": 28, "relative_humidity": 80},
    ).json()
    assert cold["band"] == "dry"
    assert warm["band"] == "very_humid"


# --- scan -----------------------------------------------------------------


def test_scan_requires_photo_consent_and_nothing_else_breaks_without_it(client) -> None:
    headers = _auth(client)
    denied = client.post("/api/v1/scans", headers=headers)
    assert denied.status_code == 403
    assert denied.json()["code"] == "consent_required"

    # El resto de la app sigue funcionando sin ese consentimiento.
    assert client.get("/api/v1/profile", headers=headers).status_code == 200
    assert client.get("/api/v1/education/myths").status_code == 200


def test_full_scan_flow_declares_the_missing_vision_model(client) -> None:
    headers = _auth(client)
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]

    quality = client.post(
        f"/api/v1/scans/{scan_id}/photos",
        headers=headers,
        data={"angle": "front", "face_cropped": "false"},
        files={"file": ("front.jpg", _photo_bytes(), "image/jpeg")},
    ).json()
    assert quality["must_retake"] is False

    result = client.post(f"/api/v1/scans/{scan_id}/analyse", headers=headers).json()
    stages = {s["stage"]: s["status"] for s in result["stages"]}
    assert stages["segmentation"] == "unavailable"
    assert result["used_image_analysis"] is False
    assert result["estimates"] == {}
    assert result["requires_user_confirmation"] is True
    assert result["explanation"]["params"]["segmentation_is_mock"] is True


def test_scan_reports_which_photo_to_retake(client) -> None:
    headers = _auth(client)
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]
    dark = io.BytesIO()
    Image.fromarray(np.full((900, 900, 3), 3, dtype=np.uint8)).save(dark, format="JPEG")
    quality = client.post(
        f"/api/v1/scans/{scan_id}/photos",
        headers=headers,
        data={"angle": "crown_top"},
        files={"file": ("dark.jpg", dark.getvalue(), "image/jpeg")},
    ).json()
    assert quality["must_retake"] is True
    assert any(i["code"] == "underexposed" for i in quality["issues"])


def test_scan_confirmation_records_user_corrections(client) -> None:
    headers = _auth(client)
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]
    client.post(
        f"/api/v1/scans/{scan_id}/photos",
        headers=headers,
        data={"angle": "front"},
        files={"file": ("front.jpg", _photo_bytes(), "image/jpeg")},
    )
    client.post(f"/api/v1/scans/{scan_id}/analyse", headers=headers)

    confirmed = client.post(
        f"/api/v1/scans/{scan_id}/confirm",
        headers=headers,
        json={"crown": {"porosity": "high"}},
    ).json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["outcomes"]["crown"]["porosity"] == "user_correction"

    zones = client.get("/api/v1/profile/zones", headers=headers).json()
    crown = next(z for z in zones if z["zone"] == "crown")
    assert crown["measurements"]["porosity"]["source"] == "user"


# --- inventario y aprendizaje --------------------------------------------


def test_ingredient_scanner_explains_by_function(client) -> None:
    headers = _auth(client)
    response = client.post(
        "/api/v1/inventory/scan-ingredients",
        headers=headers,
        json={"inci": "Aqua, Dimethicone, Cetearyl Alcohol, Alcohol Denat, Glycerin"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    functions = {i["inci_name"]: i["functions"] for i in body["ingredients"]}
    assert functions["Dimethicone"] == ["silicone_insoluble"]
    assert "alcohol_fatty" in functions["Cetearyl Alcohol"]
    assert functions["Alcohol Denat"] == ["alcohol_drying"]


def test_duplicate_detection_discourages_buying_more_of_the_same(client) -> None:
    headers = _auth(client)
    for index in range(2):
        client.post(
            "/api/v1/inventory",
            headers=headers,
            json={"custom_name": f"gel {index}", "custom_category": "gel"},
        )
    duplicates = client.get("/api/v1/inventory/duplicates", headers=headers).json()
    assert duplicates and duplicates[0]["category"] == "gel"


def test_insights_say_they_are_still_learning_when_data_is_thin(client) -> None:
    headers = _auth(client)
    body = client.get("/api/v1/journal/insights", headers=headers).json()
    assert body["has_enough_data"] is False
    assert body["message_key"] == "learning.still_learning_about_you"


def test_cold_start_is_reported_honestly(client) -> None:
    headers = _auth(client)
    body = client.get("/api/v1/journal/cold-start", headers=headers).json()
    assert body["stage"] == "no_data"
    assert body["based_on_reference_profiles"] is False
    assert body["explanation"]["personal_confidence"] == 0.0
    assert body["milestone_keys"]


def test_journal_entry_and_twin_flow(client) -> None:
    headers = _auth(client)
    for index in range(8):
        client.post(
            "/api/v1/journal",
            headers=headers,
            json={"entry_date": (date(2026, 1, 1) + timedelta(days=index * 7)).isoformat()},
        )
    entries = client.get("/api/v1/journal", headers=headers).json()
    assert len(entries) == 8

    twin = client.get("/api/v1/twin", headers=headers).json()
    assert twin["entry_count"] == 8
    # Sin valoraciones registradas el twin no inventa rasgos.
    assert twin["completeness"] == 0.0


def test_projection_without_history_says_what_to_log(client) -> None:
    headers = _auth(client)
    body = client.get(
        "/api/v1/twin/project", headers=headers, params={"scenario": "higher_humidity"}
    ).json()
    assert body["can_project"] is False
    assert body["missing_data_keys"]


def test_billing_entitlements_show_what_is_always_included(client) -> None:
    headers = _auth(client, email="plan@example.com")
    body = client.get("/api/v1/billing/entitlements", headers=headers).json()
    assert body["plan"] == "free"
    always = {f["feature"] for f in body["always_included"]}
    # Lo que la persona ya generó nunca está detrás del muro.
    assert {"journal_entry", "data_export", "explanation"} <= always


def test_scan_quota_is_charged_only_when_the_analysis_succeeds(client) -> None:
    headers = _auth(client, email="cupo@example.com")
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]

    # Crear el scan no descuenta: podría no llegar a analizarse nunca.
    assert client.get(
        "/api/v1/billing/check", headers=headers, params={"feature": "scan"}
    ).json()["used"] == 0

    client.post(
        f"/api/v1/scans/{scan_id}/photos",
        headers=headers,
        data={"angle": "front"},
        files={"file": ("front.jpg", _photo_bytes(), "image/jpeg")},
    )
    client.post(f"/api/v1/scans/{scan_id}/analyse", headers=headers)

    assert client.get(
        "/api/v1/billing/check", headers=headers, params={"feature": "scan"}
    ).json()["used"] == 1


def test_free_plan_blocks_a_third_scan_before_taking_photos(client) -> None:
    """El cupo se comprueba al empezar, no después de fotografiar ocho
    ángulos."""
    headers = _auth(client, email="tope@example.com")
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    for _ in range(2):
        scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]
        client.post(
            f"/api/v1/scans/{scan_id}/photos",
            headers=headers,
            data={"angle": "front"},
            files={"file": ("front.jpg", _photo_bytes(), "image/jpeg")},
        )
        client.post(f"/api/v1/scans/{scan_id}/analyse", headers=headers)

    blocked = client.post("/api/v1/scans", headers=headers)
    assert blocked.status_code == 403
    assert blocked.json()["details"]["reason"] == "quota_exhausted"

    # Y el diario sigue abierto: los datos propios nunca se limitan.
    assert client.get("/api/v1/journal", headers=headers).status_code == 200


def test_subscribing_lifts_the_limits(client) -> None:
    headers = _auth(client, email="suscrito@example.com")
    activated = client.post(
        "/api/v1/billing/activate",
        headers=headers,
        params={
            "plan": "studio",
            "store": "app_store",
            "store_transaction_id": "tx-123",
            "period_end": "2099-12-31",
            "billing_country": "MX",
        },
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["plan"] == "studio"

    scan = client.get("/api/v1/billing/check", headers=headers, params={"feature": "scan"}).json()
    assert scan["limit"] is None


def test_cancelling_keeps_the_plan_until_the_period_ends(client) -> None:
    headers = _auth(client, email="cancela@example.com")
    client.post(
        "/api/v1/billing/activate",
        headers=headers,
        params={
            "plan": "studio",
            "store": "play_store",
            "store_transaction_id": "tx-9",
            "period_end": "2099-12-31",
        },
    )
    cancelled = client.post("/api/v1/billing/cancel", headers=headers).json()
    assert cancelled["plan"] == "studio"
    assert cancelled["renews"] is False


def test_pro_plan_is_not_self_serve(client) -> None:
    headers = _auth(client, email="pro@example.com")
    response = client.post(
        "/api/v1/billing/activate",
        headers=headers,
        params={
            "plan": "pro",
            "store": "app_store",
            "store_transaction_id": "tx-1",
            "period_end": "2099-12-31",
        },
    )
    assert response.status_code == 403


def test_free_tier_limits_active_experiments_without_blocking_data(client) -> None:
    headers = _auth(client)
    arms = [{"label_key": "arm.a"}, {"label_key": "arm.b"}]
    first = client.post(
        "/api/v1/experiments", headers=headers, json={"question_key": "q1", "arms": arms}
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/v1/experiments", headers=headers, json={"question_key": "q2", "arms": arms}
    )
    assert second.status_code == 403
    assert second.json()["details"]["feature"] == "active_experiment"
    # El diario, que son datos de la persona, nunca se limita.
    assert client.get("/api/v1/journal", headers=headers).status_code == 200


# --- educación ------------------------------------------------------------


def test_myths_are_exposed_with_their_correction(client) -> None:
    myths = client.get("/api/v1/education/myths").json()
    assert len(myths) >= 6
    for myth in myths:
        assert myth["evidence_level"] == "unsupported_trend"
        assert myth["mechanism"]


def test_every_rule_is_auditable_with_its_provenance(client) -> None:
    """Que las reglas sean consultables es parte del producto (A21/B4)."""
    rules = client.get("/api/v1/education/rules").json()
    assert len(rules) > 20
    for rule in rules:
        assert rule["evidence_level"]
        assert rule["evidence_label_key"]


# --- borrado de cuenta (A22) ---------------------------------------------


def test_account_deletion_removes_rows_and_stored_photos(client, tmp_path) -> None:
    headers = _auth(client)
    client.put(
        "/api/v1/auth/consents",
        headers=headers,
        json=[{"purpose": "photo_processing", "granted": True}],
    )
    scan_id = client.post("/api/v1/scans", headers=headers).json()["id"]
    client.post(
        f"/api/v1/scans/{scan_id}/photos",
        headers=headers,
        data={"angle": "front"},
        files={"file": ("front.jpg", _photo_bytes(), "image/jpeg")},
    )

    storage_root = tmp_path / "storage"
    assert list(storage_root.rglob("*.jpg")), "la foto debería estar almacenada"

    assert client.delete("/api/v1/auth/account", headers=headers).status_code == 204

    assert not list(storage_root.rglob("*.jpg")), "el borrado debe purgar el storage, no solo filas"
    assert client.get("/api/v1/profile", headers=headers).status_code == 401


# --- durabilidad de la transacción ----------------------------------------


def test_a_successful_response_means_the_data_is_already_committed(client) -> None:
    """La transacción se confirma **antes** de responder.

    Con el patrón habitual (`commit` en la limpieza de la dependencia) el
    commit ocurre después de generar la respuesta: el cliente recibe un 204 de
    borrado de cuenta y, si vuelve a preguntar de inmediato, la cuenta sigue
    ahí. Peor todavía: si el commit falla, ya se le dijo que fue bien.
    """
    headers = _auth(client, email="durabilidad@example.com")

    assert client.delete("/api/v1/auth/account", headers=headers).status_code == 204
    # Sin ninguna espera: si la respuesta llegó, el borrado ya es firme.
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_created_resources_are_readable_immediately(client) -> None:
    headers = _auth(client, email="inmediato@example.com")
    created = client.post(
        "/api/v1/journal", headers=headers, json={"entry_date": "2026-05-01"}
    )
    assert created.status_code == 201
    listed = client.get("/api/v1/journal", headers=headers).json()
    assert [entry["id"] for entry in listed] == [created.json()["id"]]


def test_a_failed_request_leaves_nothing_behind(client) -> None:
    """Un fallo a mitad no puede dejar filas a medias."""
    headers = _auth(client, email="rollback@example.com")
    before = client.get("/api/v1/profile", headers=headers).json()

    rejected = client.put(
        "/api/v1/profile/goals", headers=headers, json={"goals": ["objetivo_inexistente"]}
    )
    assert rejected.status_code == 422

    after = client.get("/api/v1/profile", headers=headers).json()
    assert after["goals"] == before["goals"]
