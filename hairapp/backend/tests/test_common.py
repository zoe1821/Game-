from datetime import date

import pytest

from app.domain.common import (
    Measured,
    MeasurementError,
    Source,
    Unavailable,
    resolve,
    user_value,
)


def test_source_ceilings_prevent_overconfident_estimates() -> None:
    with pytest.raises(MeasurementError):
        Measured("3a", Source.AI_VISION, 0.99)
    with pytest.raises(MeasurementError):
        Measured("3a", Source.DEFAULT, 0.5)
    # La confirmación de la persona sí puede llegar a 1.0.
    assert user_value("3a").confidence == 1.0


def test_user_correction_always_wins_over_newer_ai_estimate() -> None:
    """A1.4: el motor nunca sobrescribe una corrección manual, ni con datos
    más recientes ni con más confianza."""
    ai = Measured("3a", Source.AI_VISION, 0.85, date(2026, 8, 1))
    manual = user_value("3c", observed_at=date(2025, 1, 1))
    assert resolve([ai, manual]).value == "3c"
    assert resolve([manual, ai]).value == "3c"


def test_resolve_prefers_higher_confidence_within_same_source() -> None:
    low = Measured("a", Source.INFERRED, 0.3, date(2026, 1, 1))
    high = Measured("b", Source.INFERRED, 0.7, date(2026, 1, 1))
    assert resolve([low, high]).value == "b"


def test_resolve_empty_is_none() -> None:
    assert resolve([]) is None


def test_unavailable_carries_a_reason() -> None:
    unavailable = Unavailable("no_segmentation_model")
    assert unavailable.reason_key == "no_segmentation_model"
