from app.domain.common import Source
from app.domain.hair.attributes import Density, Porosity, ProcessingState
from app.domain.hair.estimation import (
    DensityInputs,
    ElasticityTest,
    PorosityInputs,
    estimate_density,
    estimate_elasticity,
    estimate_porosity,
)
from app.domain.hair.zones import ALL_ZONES, PhotoAngle, Zone, coverage_for


def test_porosity_never_relies_on_a_single_signal() -> None:
    single, signals = estimate_porosity(PorosityInputs(dries_quickly=True))
    many, many_signals = estimate_porosity(
        PorosityInputs(
            processing=ProcessingState.BLEACHED,
            dries_quickly=True,
            frizzes_in_humidity=True,
            feels_rough_when_dry=True,
        )
    )
    assert len(many_signals) > len(signals)
    assert many.confidence > single.confidence


def test_no_signals_means_no_estimate_not_a_guess() -> None:
    measured, signals = estimate_porosity(PorosityInputs())
    assert signals == []
    assert measured.confidence == 0.0
    assert measured.source is Source.DEFAULT
    assert measured.notes == "no_signals_available"


def test_conflicting_signals_lower_confidence() -> None:
    agreeing, _ = estimate_porosity(
        PorosityInputs(processing=ProcessingState.BLEACHED, dries_quickly=True)
    )
    conflicting, _ = estimate_porosity(
        PorosityInputs(processing=ProcessingState.BLEACHED, dries_quickly=False, wets_slowly=True)
    )
    assert conflicting.confidence < agreeing.confidence


def test_estimates_never_reach_certainty() -> None:
    measured, _ = estimate_porosity(
        PorosityInputs(
            processing=ProcessingState.BLEACHED,
            dries_quickly=True,
            frizzes_in_humidity=True,
            feels_rough_when_dry=True,
            absorbs_product_fast=True,
            heat_use_per_week=5,
        )
    )
    assert measured.confidence < 1.0
    assert measured.confidence <= Source.INFERRED.confidence_ceiling


def test_transitioning_hair_is_mixed_porosity_not_averaged() -> None:
    measured, _ = estimate_porosity(PorosityInputs(processing=ProcessingState.TRANSITIONING))
    assert measured.value is Porosity.MIXED


def test_user_reported_density_wins_and_is_certain() -> None:
    measured = estimate_density(
        DensityInputs(ponytail_circumference_cm=3.0, user_reported=Density.HIGH)
    )
    assert measured.value is Density.HIGH
    assert measured.source is Source.USER
    assert measured.confidence == 1.0


def test_density_signals_that_disagree_reduce_confidence() -> None:
    agree = estimate_density(
        DensityInputs(ponytail_circumference_cm=12.0, scalp_visible_when_parted=False)
    )
    disagree = estimate_density(
        DensityInputs(ponytail_circumference_cm=12.0, scalp_visible_when_parted=True)
    )
    assert disagree.confidence < agree.confidence


def test_elasticity_detects_the_excessive_case() -> None:
    measured = estimate_elasticity(ElasticityTest(stretch_ratio=1.8, returns_to_length=False))
    assert measured.value.value == "excessive"


def test_missing_photo_angles_leave_zones_honestly_uncovered() -> None:
    """A3/A4: si no se vio una zona, se dice; no se estima igualmente."""
    coverage = coverage_for([PhotoAngle.FRONT, PhotoAngle.CROWN_TOP])
    assert not coverage.is_complete
    assert Zone.NAPE in coverage.uncovered


def test_full_angle_set_covers_every_zone() -> None:
    coverage = coverage_for(list(PhotoAngle))
    assert coverage.is_complete
    assert coverage.covered == frozenset(ALL_ZONES)
