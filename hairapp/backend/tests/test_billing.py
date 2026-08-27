"""Las reglas duras del paywall, como tests.

Están en docs/02-MONETIZATION.md §2. No son buenas intenciones: si alguien las
rompe, el build falla.
"""

from __future__ import annotations

import ast
import inspect
from datetime import date
from pathlib import Path

import pytest

from app.domain.billing import entitlements
from app.domain.billing.entitlements import (
    Feature,
    Plan,
    Reason,
    Subscription,
    check,
    quota,
)

TODAY = date(2026, 8, 15)


# --- Regla 1: los datos propios nunca se bloquean -------------------------


def test_own_data_is_never_limited_in_any_plan() -> None:
    """Si cancela, conserva todo su histórico. Solo pierde análisis nuevo."""
    for plan in Plan:
        for feature in Feature:
            if not feature.is_own_data:
                continue
            decision = check(plan, feature, used_this_period=10_000)
            assert decision.allowed, f"{plan.value}/{feature.value}"
            assert decision.limit is None


def test_journal_and_export_survive_downgrade() -> None:
    for feature in (Feature.JOURNAL_ENTRY, Feature.DATA_EXPORT, Feature.ZONE_CORRECTION):
        assert check(Plan.FREE, feature, used_this_period=999).allowed


# --- Regla 2: la explicabilidad nunca es premium --------------------------


def test_explanation_is_free_forever() -> None:
    """Cobrar por el «¿por qué esto?» sería el patrón oscuro que este producto
    existe para evitar."""
    assert Feature.EXPLANATION.is_own_data
    assert quota(Plan.FREE, Feature.EXPLANATION) is None
    assert check(Plan.FREE, Feature.EXPLANATION, used_this_period=10_000).allowed


def test_education_is_free_forever() -> None:
    assert quota(Plan.FREE, Feature.EDUCATION) is None


# --- El tier gratuito tiene que servir de verdad --------------------------


def test_free_tier_can_actually_care_for_hair() -> None:
    """Si el gratuito no sirve, la promesa educativa del producto es falsa."""
    for feature in (Feature.SCAN, Feature.INGREDIENT_SCAN, Feature.ACTIVE_ROUTINE):
        limit = quota(Plan.FREE, feature)
        assert limit is None or limit > 0, feature.value


# --- Cupo -----------------------------------------------------------------


def test_quota_is_enforced_and_reports_what_is_left() -> None:
    allowed = check(Plan.FREE, Feature.SCAN, used_this_period=1)
    assert allowed.allowed and allowed.remaining == 1

    exhausted = check(Plan.FREE, Feature.SCAN, used_this_period=2)
    assert not exhausted.allowed
    assert exhausted.reason is Reason.QUOTA_EXHAUSTED
    assert exhausted.remaining == 0


def test_features_absent_from_the_free_plan_say_so_distinctly() -> None:
    """«No está en tu plan» y «se te acabó el cupo» son cosas distintas y la
    interfaz las cuenta distinto."""
    decision = check(Plan.FREE, Feature.STYLIST_REPORT)
    assert not decision.allowed
    assert decision.reason is Reason.NOT_IN_PLAN


def test_paid_plan_lifts_the_analysis_limits() -> None:
    for feature in (Feature.SCAN, Feature.INGREDIENT_SCAN, Feature.TWIN_PROJECTION):
        assert quota(Plan.STUDIO, feature) is None


def test_assistant_keeps_a_quota_even_when_paid() -> None:
    """Es el único coste que escala mal. Un cupo honesto es mejor que degradar
    la calidad en silencio (docs/02-MONETIZATION.md §6)."""
    assert quota(Plan.STUDIO, Feature.ASSISTANT_QUERY) is not None


# --- Suscripción ----------------------------------------------------------


def test_cancelling_keeps_access_until_the_paid_period_ends() -> None:
    """Cortar antes sería quedarse con dinero por un servicio no prestado."""
    subscription = Subscription(
        Plan.STUDIO, date(2026, 8, 1), date(2026, 8, 31), cancelled_at=date(2026, 8, 10)
    )
    assert subscription.effective_plan_on(date(2026, 8, 20)) is Plan.STUDIO
    assert subscription.effective_plan_on(date(2026, 9, 5)) is Plan.FREE
    assert not subscription.renews


def test_grace_period_keeps_access_while_the_store_retries() -> None:
    subscription = Subscription(
        Plan.STUDIO, date(2026, 7, 1), date(2026, 7, 31), in_grace_period=True
    )
    assert subscription.effective_plan_on(TODAY) is Plan.STUDIO


def test_free_plan_is_always_active() -> None:
    subscription = Subscription(Plan.FREE, date(2026, 1, 1), date(2026, 1, 31))
    assert subscription.effective_plan_on(date(2030, 1, 1)) is Plan.FREE


# --- Separación estructural respecto del motor de producto ----------------


def test_the_product_engine_cannot_see_billing() -> None:
    """docs/02-MONETIZATION.md §4: el ranking de producto no puede leer nada
    relacionado con ingresos, ni siquiera de forma indirecta."""
    from app.domain.products import catalog, matching

    for module in (matching, catalog):
        source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert "billing" not in name, f"{module.__name__} importa {name}"
                assert "entitlement" not in name, f"{module.__name__} importa {name}"


def test_billing_module_does_not_import_the_product_engine() -> None:
    """Y al revés: el módulo de cobro no decide nada sobre productos."""
    source = Path(inspect.getfile(entitlements)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "products" not in node.module


@pytest.mark.parametrize("plan", list(Plan))
def test_every_feature_has_a_defined_position_in_every_plan(plan: Plan) -> None:
    """Ninguna función puede quedar sin decidir: un olvido acabaría siendo
    gratis o de pago por accidente."""
    for feature in Feature:
        # No lanza y devuelve None (ilimitado) o un entero.
        limit = quota(plan, feature)
        assert limit is None or isinstance(limit, int)
