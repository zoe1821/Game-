"""El glosario controlado es un requisito legal ejecutable (B6)."""

from app.domain.evidence.language import ControlledLanguage, errors


def test_medical_terms_are_blocked(language: ControlledLanguage) -> None:
    findings = errors(language.check("Esto puede tratar la dermatitis", location="t"))
    terms = {f.term for f in findings}
    assert "dermatitis" in terms
    assert "tratar" in terms


def test_accents_and_case_do_not_evade_the_checker(language: ControlledLanguage) -> None:
    assert errors(language.check("INFECCION", location="t"))
    assert errors(language.check("Infección", location="t"))


def test_substring_does_not_false_positive(language: ControlledLanguage) -> None:
    """«contratar» contiene «tratar» pero no es el término bloqueado."""
    assert not errors(language.check("Vas a contratar a alguien", location="t"))


def test_imperatives_blocked_only_in_prescriptive_context(language: ControlledLanguage) -> None:
    text = "Debes aplicar el gel"
    assert not errors(language.check(text, location="edu", prescriptive=False))
    assert errors(language.check(text, location="routine.step", prescriptive=True))


def test_neutral_cosmetic_language_passes(language: ControlledLanguage) -> None:
    text = "Aplica el gel en la coronilla y define con las manos. Puedes considerar difundir."
    assert not errors(language.check(text, location="t", prescriptive=True))


def test_rule_packs_contain_no_blocked_language(rules, language: ControlledLanguage) -> None:
    """Si esto falla, el pack no debe desplegarse. Ver docs/04-LEGAL-CHECKLIST.md §8.6."""
    findings = []
    for rule in rules:
        findings += errors(language.check(rule.mechanism, location=f"rule:{rule.id}"))
    assert findings == [], "\n".join(str(f) for f in findings)
