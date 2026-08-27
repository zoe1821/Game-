"""Crecimiento y retención: la distinción que la categoría suele confundir."""

from __future__ import annotations

from datetime import date

from app.domain.hair.growth import (
    GrowthSource,
    LengthObservation,
    expected_length,
    read_growth,
)


def _reading(gain: float, months: int = 6, **kwargs):
    return read_growth(
        [
            LengthObservation(date(2026, 1, 1), 30.0),
            LengthObservation(date(2026, 1 + months, 1), 30.0 + gain, **kwargs),
        ]
    )


def test_slow_visible_gain_is_reported_as_breakage_not_slow_growth() -> None:
    """El caso más frecuente: alguien cree que su cabello «no crece» cuando en
    realidad crece igual que siempre y se rompe por abajo."""
    reading = _reading(1.0)
    assert reading is not None
    assert reading.is_retention_problem
    assert reading.lost_to_breakage_cm > 5
    assert reading.retention_ratio < 0.3


def test_assumed_growth_rate_is_declared_as_assumed() -> None:
    """La longitud sola no puede medir el crecimiento: 1 cm en seis meses es
    compatible con crecer poco y con romperse mucho."""
    reading = _reading(1.0)
    assert reading is not None
    assert reading.growth_source is GrowthSource.ASSUMED_POPULATION
    assert not reading.growth_is_measured
    assert "uncertainty.growth_rate_assumed_not_measured" in reading.explanation.uncertainty_keys
    assert "growth.alternative.measure_root_regrowth" in reading.explanation.alternatives


def test_root_regrowth_turns_an_assumption_into_a_measurement() -> None:
    """En cabello teñido, la distancia a la línea de color sí mide el
    crecimiento de verdad."""
    assumed = _reading(1.0)
    measured = _reading(1.0, root_regrowth_cm=2.0)
    assert assumed is not None and measured is not None

    assert measured.growth_is_measured
    assert measured.growth_source is GrowthSource.MEASURED_AT_ROOT
    # Y se nota en la confianza: una medición vale más que un supuesto.
    assert measured.explanation.evidence_confidence > assumed.explanation.evidence_confidence


def test_a_deliberate_trim_is_not_counted_as_breakage() -> None:
    """Cortar es una decisión, no una pérdida."""
    reading = _reading(4.5, trimmed_cm=3.0)
    assert reading is not None
    assert reading.retention_ratio > 0.9
    assert not reading.is_retention_problem


def test_healthy_retention_is_not_flagged() -> None:
    reading = _reading(7.0)
    assert reading is not None
    assert not reading.is_retention_problem


def test_too_short_a_period_returns_nothing() -> None:
    """Entre dos mediciones caseras con tres semanas de diferencia, lo que se
    mide es cómo se estiró el pelo, no el crecimiento."""
    assert (
        read_growth(
            [
                LengthObservation(date(2026, 1, 1), 30.0),
                LengthObservation(date(2026, 1, 20), 30.5),
            ]
        )
        is None
    )


def test_a_single_measurement_returns_nothing() -> None:
    assert read_growth([LengthObservation(date(2026, 1, 1), 30.0)]) is None


def test_expected_length_is_a_range_not_a_number() -> None:
    """Dar una cifra exacta sería falsa precisión: la velocidad varía entre
    personas."""
    low, high = expected_length(30.0, 12)
    assert low < high
    assert low > 30.0


def test_confidence_grows_with_more_measurements_over_more_time() -> None:
    short = read_growth(
        [
            LengthObservation(date(2026, 1, 1), 30.0),
            LengthObservation(date(2026, 4, 1), 32.0),
        ]
    )
    long = read_growth(
        [LengthObservation(date(2026, month, 1), 30.0 + month) for month in range(1, 9)]
    )
    assert short is not None and long is not None
    assert long.explanation.personal_confidence > short.explanation.personal_confidence
