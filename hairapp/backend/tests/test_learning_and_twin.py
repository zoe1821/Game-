from datetime import date, timedelta

from app.domain.climate.weather import (
    DewPointBand,
    Weather,
    assess_water,
    classify_hardness,
    forecast,
)
from app.domain.experiments.engine import (
    Experiment,
    ExperimentArm,
    ExperimentStatus,
    read_experiment,
)
from app.domain.hair.attributes import Density, Porosity, StrandDiameter
from app.domain.learning.cold_start import (
    ColdStartStage,
    ReferenceProfile,
    guidance,
    stage_for,
)
from app.domain.learning.journal import JournalEntry, Strength, analyse_journal
from app.domain.learning.journal import ResultRating as R
from app.domain.twin.model import TraitKey, build_twin
from app.domain.twin.projection import Direction, Scenario, project

BASE = date(2026, 1, 1)


def _entry(index: int, *, products: tuple[str, ...], dew: float, d1: R, d2: R, arm: str | None = None) -> JournalEntry:
    return JournalEntry(
        id=f"j{index}-{arm or 'x'}",
        date=BASE + timedelta(days=index * 7),
        product_ids=products,
        dew_point_c=dew,
        rating_day1=d1,
        rating_day2=d2,
        experiment_arm_id=arm,
    )


# --- clima ----------------------------------------------------------------


def test_dew_point_not_relative_humidity_drives_the_forecast() -> None:
    """80 % de humedad a 5 °C es aire seco para el cabello; a 28 °C no."""
    cold = Weather(temperature_c=5, relative_humidity=80)
    warm = Weather(temperature_c=28, relative_humidity=80)
    assert cold.relative_humidity == warm.relative_humidity
    assert forecast(cold).band is DewPointBand.DRY
    assert forecast(warm).band is DewPointBand.VERY_HUMID


def test_high_porosity_raises_frizz_risk_at_the_same_weather() -> None:
    weather = Weather(temperature_c=24, relative_humidity=75)
    assert forecast(weather, porosity="high").frizz_risk > forecast(weather, porosity="low").frizz_risk


def test_water_without_any_signal_returns_nothing_rather_than_a_default() -> None:
    assert assess_water() is None


def test_estimated_water_declares_that_it_is_an_estimate() -> None:
    assessment = assess_water(reports_limescale=True, soap_lathers_poorly=True)
    assert assessment is not None
    assert assessment.estimated
    assert "uncertainty.water_estimated_not_measured" in assessment.explanation.uncertainty_keys


def test_hardness_bands() -> None:
    assert classify_hardness(30).value == "soft"
    assert classify_hardness(250).value == "very_hard"


# --- aprendizaje del diario ----------------------------------------------


def test_no_conclusions_below_the_minimum_sample() -> None:
    entries = [_entry(i, products=("gelA",), dew=15, d1=R.GREAT, d2=R.GOOD) for i in range(3)]
    assert analyse_journal(entries) == []


def test_findings_always_report_sample_size_and_uncertainty() -> None:
    entries = [_entry(i, products=("gelA",), dew=15 + i * 0.2, d1=R.GREAT, d2=R.GOOD) for i in range(6)]
    entries += [_entry(20 + i, products=("gelB",), dew=15 + i * 0.2, d1=R.MEH, d2=R.BAD) for i in range(6)]
    findings = analyse_journal(entries)
    assert findings
    for finding in findings:
        assert finding.with_n + finding.without_n == finding.explanation.sample_size
        assert "uncertainty.correlation_not_causation" in finding.explanation.uncertainty_keys


def test_a_confounded_comparison_is_downgraded() -> None:
    """Si el gel A se usó siempre en días secos, la comparación no aísla el gel."""
    clean = [_entry(i, products=("gelA",), dew=15, d1=R.GREAT, d2=R.GOOD) for i in range(8)]
    clean += [_entry(20 + i, products=("gelB",), dew=15.5, d1=R.MEH, d2=R.BAD) for i in range(8)]
    confounded = [_entry(i, products=("gelA",), dew=6, d1=R.GREAT, d2=R.GOOD) for i in range(8)]
    confounded += [_entry(20 + i, products=("gelB",), dew=24, d1=R.MEH, d2=R.BAD) for i in range(8)]

    clean_finding = next(f for f in analyse_journal(clean) if f.subject == "gelA")
    confounded_finding = next(f for f in analyse_journal(confounded) if f.subject == "gelA")

    assert clean_finding.strength is Strength.STRONG
    assert confounded_finding.strength is not Strength.STRONG
    assert "dew_point" in confounded_finding.uncontrolled_variables


# --- cold start (B2) ------------------------------------------------------


def test_cold_start_stages() -> None:
    assert stage_for(0) is ColdStartStage.NO_DATA
    assert stage_for(2) is ColdStartStage.FIRST_STEPS
    assert stage_for(4) is ColdStartStage.EARLY_PATTERN
    assert stage_for(20) is ColdStartStage.ESTABLISHED


def test_reference_profiles_are_labelled_as_not_your_history() -> None:
    from app.domain.common import Measured, Source

    reference = ReferenceProfile(
        "r1", Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, "3", sample_size=140,
        top_techniques=("praying_hands",),
    )
    result = guidance(
        entry_count=0,
        porosity=Measured(Porosity.HIGH, Source.INFERRED, 0.6),
        density=Measured(Density.MEDIUM, Source.INFERRED, 0.5),
        strand_diameter=Measured(StrandDiameter.FINE, Source.INFERRED, 0.5),
        pattern_family="3",
        reference_profiles=[reference],
    )
    assert result.is_based_on_reference_profiles
    assert result.explanation.personal_confidence == 0.0
    assert "uncertainty.not_your_history" in result.explanation.uncertainty_keys
    assert result.reference_sample_size == 140


def test_without_consent_no_reference_profile_is_used() -> None:
    """A22/B7: sin consentimiento separado no se usan datos agregados de nadie."""
    reference = ReferenceProfile(
        "r1", Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, "3", sample_size=140
    )
    result = guidance(
        entry_count=0, pattern_family="3", reference_profiles=[reference],
        consented_to_reference_profiles=False,
    )
    assert not result.is_based_on_reference_profiles
    assert result.message_key == "cold_start.general_consensus_only"


def test_tiny_reference_aggregates_are_not_used() -> None:
    reference = ReferenceProfile(
        "r1", Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, "3", sample_size=4
    )
    result = guidance(entry_count=0, pattern_family="3", reference_profiles=[reference])
    assert not result.is_based_on_reference_profiles


def test_cold_start_always_offers_a_next_step() -> None:
    for count in (0, 1, 4, 8, 30):
        assert guidance(entry_count=count).milestone_keys


# --- experimentos (A25) ---------------------------------------------------


def _experiment() -> Experiment:
    return Experiment(
        id="e1",
        question_key="q",
        arms=(
            ExperimentArm("a", "arm.a", product_ids=("crema", "gel")),
            ExperimentArm("b", "arm.b", product_ids=("gel",)),
        ),
        controlled_variables=("dew_point", "other_products"),
    )


def test_experiment_waits_instead_of_declaring_an_early_winner() -> None:
    entries = [_entry(i, products=("crema", "gel"), dew=15, d1=R.GREAT, d2=R.GOOD, arm="a") for i in range(2)]
    entries += [_entry(10 + i, products=("gel",), dew=15, d1=R.MEH, d2=R.MEH, arm="b") for i in range(4)]
    reading = read_experiment(_experiment(), entries)
    assert reading.status is ExperimentStatus.RUNNING
    assert reading.winner_arm_id is None
    assert reading.explanation.params["missing_repetitions"]["a"] == 1


def test_broken_control_invalidates_the_reading() -> None:
    entries = [_entry(i, products=("crema", "gel"), dew=6, d1=R.GREAT, d2=R.GOOD, arm="a") for i in range(4)]
    entries += [_entry(10 + i, products=("gel",), dew=24, d1=R.MEH, d2=R.MEH, arm="b") for i in range(4)]
    reading = read_experiment(_experiment(), entries)
    assert reading.status is ExperimentStatus.INVALID
    assert reading.winner_arm_id is None
    assert any(i.key == "declared_control_broken" for i in reading.protocol_issues)


def test_a_tie_is_reported_as_a_tie() -> None:
    entries = [_entry(i, products=("crema", "gel"), dew=15, d1=R.GOOD, d2=R.GOOD, arm="a") for i in range(4)]
    entries += [_entry(10 + i, products=("gel",), dew=15, d1=R.GOOD, d2=R.GOOD, arm="b") for i in range(4)]
    reading = read_experiment(_experiment(), entries)
    assert reading.status is ExperimentStatus.CONCLUDED
    assert reading.winner_arm_id is None
    assert not reading.is_conclusive
    assert "uncertainty.difference_within_noise" in reading.explanation.uncertainty_keys


def test_a_clean_experiment_concludes() -> None:
    entries = [_entry(i, products=("crema", "gel"), dew=15, d1=R.GREAT, d2=R.GOOD, arm="a") for i in range(4)]
    entries += [_entry(10 + i, products=("gel",), dew=15, d1=R.MEH, d2=R.BAD, arm="b") for i in range(4)]
    reading = read_experiment(_experiment(), entries)
    assert reading.is_conclusive
    assert reading.winner_arm_id == "a"


def test_an_experiment_needs_at_least_two_arms() -> None:
    import pytest

    with pytest.raises(ValueError):
        Experiment(id="x", question_key="q", arms=(ExperimentArm("only", "arm"),))


# --- digital twin (A24) ---------------------------------------------------


def _varied_weather_entries() -> list[JournalEntry]:
    data = [
        (6.0, R.GREAT, R.GREAT), (8.0, R.GREAT, R.GOOD), (12.0, R.GOOD, R.GOOD),
        (16.0, R.GOOD, R.MEH), (20.0, R.MEH, R.MEH), (23.0, R.MEH, R.BAD),
        (9.0, R.GREAT, R.GOOD), (21.0, R.MEH, R.BAD),
    ]
    return [_entry(i, products=("gel",), dew=d, d1=r1, d2=r2) for i, (d, r1, r2) in enumerate(data)]


def test_twin_learns_humidity_sensitivity_from_real_variation() -> None:
    twin = build_twin(profile_id="p", entries=_varied_weather_entries(), today=date(2026, 3, 1))
    trait = twin.trait(TraitKey.HUMIDITY_SENSITIVITY)
    assert trait is not None
    assert trait.value > 0.6
    assert trait.sample_size == 8


def test_twin_refuses_to_learn_without_weather_variation() -> None:
    """Sin variación de clima no hay nada que correlacionar."""
    entries = [_entry(i, products=("gel",), dew=15.0, d1=R.GOOD, d2=R.GOOD) for i in range(10)]
    twin = build_twin(profile_id="p", entries=entries)
    assert twin.trait(TraitKey.HUMIDITY_SENSITIVITY) is None


def test_empty_twin_reports_zero_completeness() -> None:
    twin = build_twin(profile_id="p", entries=[])
    assert twin.completeness == 0.0
    assert twin.known_traits == ()


def test_projection_without_history_says_so_and_says_what_to_log() -> None:
    """A24: no se proyecta sin base. La salida útil es qué registrar."""
    twin = build_twin(profile_id="p", entries=[])
    projection = project(twin, Scenario.HIGHER_HUMIDITY)
    assert not projection.can_project
    assert projection.direction is Direction.UNKNOWN
    assert projection.missing_data_keys
    assert projection.explanation.summary_key == "twin.projection.not_enough_history"


def test_projection_with_history_shows_its_basis() -> None:
    twin = build_twin(profile_id="p", entries=_varied_weather_entries(), today=date(2026, 3, 1))
    projection = project(twin, Scenario.HIGHER_HUMIDITY)
    assert projection.can_project
    assert projection.direction is Direction.LIKELY_WORSE
    assert projection.sample_size == 8
    assert "uncertainty.projection_is_not_a_prediction" in projection.explanation.uncertainty_keys


def test_projection_is_never_presented_as_general_evidence() -> None:
    twin = build_twin(profile_id="p", entries=_varied_weather_entries(), today=date(2026, 3, 1))
    projection = project(twin, Scenario.HIGHER_HUMIDITY)
    assert projection.explanation.evidence_level == "extended_anecdote"
