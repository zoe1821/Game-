"""Motor de evaluación de reglas.

Responsabilidades:
  1. Emparejar reglas contra los hechos de una zona/perfil.
  2. Resolver conflictos declarados entre reglas de forma explícita.
  3. Adjuntar a cada regla que sobrevive su reporte de confianza doble.

Lo que este motor **no** hace: inventar hechos que no le dan. Una condición
sobre un hecho desconocido no se cumple (ver `Condition.evaluate`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..confidence.engine import ConfidenceReport, PersonalEvidence, build_report
from ..evidence.levels import EvidenceLevel
from .model import Rule, RuleKind

#: Firma de la función que consulta el historial de la persona para una regla.
PersonalEvidenceLookup = Callable[[str], PersonalEvidence]


def no_personal_history(_rule_id: str) -> PersonalEvidence:
    """Lookup por defecto: cero historial. Es el estado de cold start (B2)."""
    return PersonalEvidence()


@dataclass(frozen=True)
class EvaluatedRule:
    rule: Rule
    confidence: ConfidenceReport
    facts_used: tuple[str, ...]
    suppressed_by: str | None = None

    @property
    def is_active(self) -> bool:
        return self.suppressed_by is None

    @property
    def effective_priority(self) -> float:
        """Prioridad ajustada por la solidez de la evidencia general.

        No se ajusta por confianza personal: si el historial de la persona
        contradice la regla, la respuesta correcta es mostrarlo, no reordenar
        en silencio. Eso lo decide la capa de rutina, con la contradicción a
        la vista.
        """
        return self.rule.priority * (0.5 + 0.5 * self.confidence.evidence_confidence)


@dataclass(frozen=True)
class EvaluationResult:
    active: tuple[EvaluatedRule, ...]
    suppressed: tuple[EvaluatedRule, ...]
    myths: tuple[Rule, ...]
    halted: bool = False
    """True si una regla de derivación detuvo el análisis (A23)."""
    halt_block_key: str | None = None

    def of_kind(self, kind: RuleKind) -> tuple[EvaluatedRule, ...]:
        return tuple(e for e in self.active if e.rule.kind is kind)

    @property
    def warnings(self) -> tuple[EvaluatedRule, ...]:
        return self.of_kind(RuleKind.WARNING)


class RuleEngine:
    def __init__(self, rules: Sequence[Rule]) -> None:
        self._rules = tuple(rules)
        self._by_id = {rule.id: rule for rule in self._rules}

    @property
    def rules(self) -> tuple[Rule, ...]:
        return self._rules

    def evaluate(
        self,
        facts: Mapping[str, Any],
        *,
        personal: PersonalEvidenceLookup = no_personal_history,
        today: date | None = None,
        extra_uncertainty: tuple[str, ...] = (),
    ) -> EvaluationResult:
        matched: list[EvaluatedRule] = []
        myths: list[Rule] = []

        for rule in self._rules:
            if rule.kind is RuleKind.MYTH:
                myths.append(rule)
                continue
            if not rule.matches(facts):
                continue
            report = build_report(
                rule.evidence_level,
                personal(rule.id),
                extra_uncertainty=extra_uncertainty,
                today=today,
            )
            matched.append(
                EvaluatedRule(
                    rule=rule,
                    confidence=report,
                    facts_used=tuple(c.fact for c in rule.conditions),
                )
            )

        # Una regla de derivación detiene el análisis por completo (A23).
        for evaluated in matched:
            if evaluated.rule.outcome.get("halt_analysis"):
                return EvaluationResult(
                    active=(evaluated,),
                    suppressed=tuple(e for e in matched if e is not evaluated),
                    myths=tuple(myths),
                    halted=True,
                    halt_block_key=str(evaluated.rule.outcome.get("show_block", "")),
                )

        active, suppressed = self._resolve_conflicts(matched)
        active.sort(key=lambda e: e.effective_priority, reverse=True)
        return EvaluationResult(
            active=tuple(active), suppressed=tuple(suppressed), myths=tuple(myths)
        )

    def _resolve_conflicts(
        self, matched: Sequence[EvaluatedRule]
    ) -> tuple[list[EvaluatedRule], list[EvaluatedRule]]:
        """Resuelve conflictos declarados en `conflicts_with`.

        Gana la de mayor prioridad efectiva. El empate se rompe por nivel de
        evidencia y, si persiste, por id, para que el resultado sea
        determinista y reproducible en tests.
        """
        by_id = {e.rule.id: e for e in matched}
        losers: dict[str, str] = {}

        for evaluated in matched:
            for other_id in evaluated.rule.conflicts_with:
                other = by_id.get(other_id)
                if other is None or other.rule.id in losers or evaluated.rule.id in losers:
                    continue
                winner, loser = _pick_winner(evaluated, other)
                losers[loser.rule.id] = winner.rule.id

        active = [e for e in matched if e.rule.id not in losers]
        suppressed = [
            EvaluatedRule(
                rule=e.rule,
                confidence=e.confidence,
                facts_used=e.facts_used,
                suppressed_by=losers[e.rule.id],
            )
            for e in matched
            if e.rule.id in losers
        ]
        return active, suppressed


def _pick_winner(a: EvaluatedRule, b: EvaluatedRule) -> tuple[EvaluatedRule, EvaluatedRule]:
    key = lambda e: (  # noqa: E731 - clave local corta y legible
        e.effective_priority,
        _EVIDENCE_ORDER[e.rule.evidence_level],
        e.rule.id,
    )
    return (a, b) if key(a) >= key(b) else (b, a)


_EVIDENCE_ORDER: dict[EvidenceLevel, int] = {
    EvidenceLevel.SCIENTIFIC_EVIDENCE: 3,
    EvidenceLevel.PROFESSIONAL_CONSENSUS: 2,
    EvidenceLevel.EXTENDED_ANECDOTE: 1,
    EvidenceLevel.UNSUPPORTED_TREND: 0,
}


def detect_myths(rules: Iterable[Rule], statements: Iterable[str]) -> list[Rule]:
    """Detector de mitos (A17): empareja afirmaciones del usuario con mitos."""
    wanted = {s.strip().lower() for s in statements}
    found = []
    for rule in rules:
        if rule.kind is not RuleKind.MYTH:
            continue
        myth_key = str(rule.outcome.get("myth", "")).lower()
        if myth_key in wanted or rule.id.lower() in wanted:
            found.append(rule)
    return found
