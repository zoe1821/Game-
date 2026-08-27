from pathlib import Path

import pytest
import yaml

from app.domain.evidence.levels import EvidenceLevel
from app.domain.rules.engine import RuleEngine, detect_myths
from app.domain.rules.loader import RulePackError, load_rule_pack
from app.domain.rules.model import RuleKind


def _write(tmp_path: Path, payload: dict) -> Path:
    target = tmp_path / "pack.yaml"
    target.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
    return target


def test_rule_without_evidence_level_does_not_load(tmp_path: Path) -> None:
    """B4: sin etiqueta la regla no carga. No hay valor por defecto silencioso."""
    path = _write(
        tmp_path,
        {
            "pack": "t",
            "version": 1,
            "rules": [{"id": "r", "kind": "routine_step", "outcome": {"step": "cleanse"}}],
        },
    )
    with pytest.raises(RulePackError, match="evidence_level"):
        load_rule_pack(path)


def test_strong_evidence_label_requires_a_mechanism(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "pack": "t",
            "version": 1,
            "rules": [
                {
                    "id": "r",
                    "kind": "routine_step",
                    "evidence_level": "scientific_evidence",
                    "outcome": {"step": "cleanse"},
                }
            ],
        },
    )
    with pytest.raises(RulePackError, match="mechanism"):
        load_rule_pack(path)


def test_single_brand_method_cannot_be_the_only_source(tmp_path: Path) -> None:
    """B4: no copiar un método único como verdad universal."""
    path = _write(
        tmp_path,
        {
            "pack": "t",
            "version": 1,
            "rules": [
                {
                    "id": "r",
                    "kind": "routine_step",
                    "evidence_level": "professional_consensus",
                    "mechanism": "porque sí",
                    "sources": ["Curly Girl Method"],
                    "outcome": {"step": "cleanse"},
                }
            ],
        },
    )
    with pytest.raises(RulePackError, match="única fuente"):
        load_rule_pack(path)


def test_duplicate_rule_ids_are_rejected(tmp_path: Path) -> None:
    rule = {
        "id": "dup",
        "kind": "education",
        "evidence_level": "extended_anecdote",
        "outcome": {"education": "x"},
    }
    path = _write(tmp_path, {"pack": "t", "version": 1, "rules": [rule, dict(rule)]})
    with pytest.raises(RulePackError, match="duplicado"):
        load_rule_pack(path)


def test_all_shipped_rules_load(rules) -> None:
    assert len(rules) > 20
    assert all(r.evidence_level is not None for r in rules)


def test_every_non_anecdotal_rule_explains_its_mechanism(rules) -> None:
    weak = {EvidenceLevel.EXTENDED_ANECDOTE, EvidenceLevel.UNSUPPORTED_TREND}
    for rule in rules:
        if rule.evidence_level not in weak:
            assert rule.mechanism, f"{rule.id} no explica su mecanismo"


def test_myths_can_never_produce_a_recommendation(rules) -> None:
    for rule in rules:
        if rule.evidence_level is EvidenceLevel.UNSUPPORTED_TREND:
            assert not rule.can_recommend


def test_unknown_facts_never_satisfy_a_condition(engine: RuleEngine) -> None:
    """No saber algo no puede contar como que se cumple."""
    result = engine.evaluate({})
    for evaluated in result.active:
        assert evaluated.rule.conditions == (), evaluated.rule.id


def test_conflicting_rules_resolve_deterministically(engine: RuleEngine) -> None:
    facts = {
        "zone.elasticity": "excessive",
        "user.reports_stiff_hair": True,
        "routine.protein_frequency_per_month": 4,
    }
    first = engine.evaluate(facts)
    second = engine.evaluate(facts)
    assert [e.rule.id for e in first.active] == [e.rule.id for e in second.active]
    suppressed = {e.rule.id for e in first.suppressed}
    assert "cond.protein_when_excessive_elasticity" in suppressed


def test_referral_signal_halts_all_analysis(engine: RuleEngine) -> None:
    """A23: ante señales que exigen evaluación profesional, no se estima nada."""
    result = engine.evaluate(
        {"scalp.referral_signs": ["inflammation"], "zone.porosity": "high"}
    )
    assert result.halted
    assert result.halt_block_key == "safety.referral_block"
    assert len(result.active) == 1


def test_myth_detector_matches_by_outcome_key(rules) -> None:
    found = detect_myths(rules, ["trimming_speeds_growth"])
    assert [r.id for r in found] == ["myth.trimming_makes_hair_grow"]


def test_shipped_packs_cover_the_expected_kinds(rules) -> None:
    kinds = {r.kind for r in rules}
    assert RuleKind.ROUTINE_STEP in kinds
    assert RuleKind.MYTH in kinds
    assert RuleKind.WARNING in kinds
