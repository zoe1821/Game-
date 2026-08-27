from datetime import date

from app.domain.confidence.engine import (
    PersonalEvidence,
    build_report,
    conflict_penalty,
    personal_confidence,
    photo_quality_penalty,
)
from app.domain.evidence.levels import EvidenceLevel

TODAY = date(2026, 8, 27)


def test_no_data_is_zero_confidence_not_half() -> None:
    """No tener datos no es «medio seguro», es no saber (B2)."""
    assert personal_confidence(PersonalEvidence(), today=TODAY) == 0.0


def test_evidence_and_personal_confidence_are_independent() -> None:
    """El eje del producto: nunca se promedian en un solo número."""
    strong_rule_no_data = build_report(
        EvidenceLevel.SCIENTIFIC_EVIDENCE, PersonalEvidence(), today=TODAY
    )
    weak_rule_lots_of_data = build_report(
        EvidenceLevel.EXTENDED_ANECDOTE,
        PersonalEvidence(supporting=14, contradicting=1, most_recent=TODAY),
        today=TODAY,
    )
    assert strong_rule_no_data.evidence_confidence > weak_rule_lots_of_data.evidence_confidence
    assert strong_rule_no_data.personal_confidence < weak_rule_lots_of_data.personal_confidence


def test_sample_size_is_always_reported() -> None:
    report = build_report(
        EvidenceLevel.PROFESSIONAL_CONSENSUS,
        PersonalEvidence(supporting=4, contradicting=2, most_recent=TODAY),
        today=TODAY,
    )
    assert report.sample_size == 6


def test_contradicting_history_is_flagged_not_hidden() -> None:
    report = build_report(
        EvidenceLevel.PROFESSIONAL_CONSENSUS,
        PersonalEvidence(supporting=1, contradicting=13, most_recent=TODAY),
        today=TODAY,
    )
    assert report.contradicts_personal_history
    assert report.personal_direction == "contradicts"
    assert "uncertainty.contradicts_your_history" in report.uncertainty_keys


def test_mixed_results_lower_confidence_and_are_declared() -> None:
    report = build_report(
        EvidenceLevel.PROFESSIONAL_CONSENSUS,
        PersonalEvidence(supporting=7, contradicting=7, most_recent=TODAY),
        today=TODAY,
    )
    assert report.personal_confidence == 0.0
    assert "uncertainty.mixed_personal_results" in report.uncertainty_keys


def test_cold_start_is_declared_below_threshold() -> None:
    report = build_report(
        EvidenceLevel.PROFESSIONAL_CONSENSUS,
        PersonalEvidence(supporting=2, most_recent=TODAY),
        today=TODAY,
    )
    assert report.is_cold_start
    assert "uncertainty.cold_start" in report.uncertainty_keys


def test_old_observations_weigh_less() -> None:
    recent = personal_confidence(
        PersonalEvidence(supporting=8, most_recent=date(2026, 8, 20)), today=TODAY
    )
    old = personal_confidence(
        PersonalEvidence(supporting=8, most_recent=date(2024, 1, 1)), today=TODAY
    )
    assert recent > old


def test_controlled_experiments_weigh_more_than_loose_observation() -> None:
    loose = personal_confidence(
        PersonalEvidence(supporting=6, most_recent=TODAY), today=TODAY
    )
    controlled = personal_confidence(
        PersonalEvidence(supporting=6, most_recent=TODAY, controlled=True), today=TODAY
    )
    assert controlled > loose


def test_penalties_are_bounded() -> None:
    assert 0.0 < photo_quality_penalty(0.0) <= 1.0
    assert photo_quality_penalty(1.0) == 1.0
    assert conflict_penalty(0) == 1.0
    assert conflict_penalty(5) < conflict_penalty(1)
