"""Modelo declarativo de reglas cosméticas.

Las reglas viven en YAML (`app/data/rules/*.yaml`), no en código, por tres
motivos: son revisables por alguien que no programa, llevan metadatos
obligatorios (etiqueta de evidencia y mecanismo) que un `if` en Python no
obligaría a escribir, y se pueden auditar en bloque.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping

from ..evidence.levels import EvidenceLevel


class RuleKind(enum.Enum):
    ROUTINE_STEP = "routine_step"
    PRODUCT_ATTRIBUTE = "product_attribute"
    TECHNIQUE = "technique"
    WARNING = "warning"
    MYTH = "myth"
    EDUCATION = "education"


class Operator(enum.Enum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS_ANY = "contains_any"
    CONTAINS_ALL = "contains_all"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    EXISTS = "exists"
    MISSING = "missing"


@dataclass(frozen=True)
class Condition:
    """Una condición sobre un hecho del contexto de evaluación."""

    fact: str
    operator: Operator
    value: Any = None

    def evaluate(self, facts: Mapping[str, Any]) -> bool:
        present = self.fact in facts
        actual = facts.get(self.fact)

        if self.operator is Operator.EXISTS:
            return present and actual is not None
        if self.operator is Operator.MISSING:
            return not present or actual is None
        if not present or actual is None:
            # Una condición sobre un hecho que no conocemos no se cumple.
            # Nunca se asume el valor favorable: eso convertiría "no sabemos"
            # en "sí", que es justamente lo que el producto no debe hacer.
            return False

        match self.operator:
            case Operator.EQ:
                return _norm(actual) == _norm(self.value)
            case Operator.NEQ:
                return _norm(actual) != _norm(self.value)
            case Operator.IN:
                return _norm(actual) in {_norm(v) for v in self.value}
            case Operator.NOT_IN:
                return _norm(actual) not in {_norm(v) for v in self.value}
            case Operator.GT:
                return float(actual) > float(self.value)
            case Operator.GTE:
                return float(actual) >= float(self.value)
            case Operator.LT:
                return float(actual) < float(self.value)
            case Operator.LTE:
                return float(actual) <= float(self.value)
            case Operator.CONTAINS_ANY:
                have = {_norm(v) for v in actual}
                return bool(have & {_norm(v) for v in self.value})
            case Operator.CONTAINS_ALL:
                have = {_norm(v) for v in actual}
                return {_norm(v) for v in self.value} <= have
            case Operator.IS_TRUE:
                return bool(actual)
            case Operator.IS_FALSE:
                return not bool(actual)
        raise AssertionError(f"operador no soportado: {self.operator}")


def _norm(value: Any) -> Any:
    """Normaliza enums a su `.value` para comparar contra YAML."""
    if isinstance(value, enum.Enum):
        return value.value
    return value


@dataclass(frozen=True)
class Rule:
    """Una regla cosmética con su procedencia obligatoria.

    `mechanism` no es opcional para reglas por encima de `EXTENDED_ANECDOTE`:
    si no sabes explicar por qué ocurre, la etiqueta máxima que puedes poner es
    anecdótica (docs/08-EVIDENCE-POLICY.md §4).
    """

    id: str
    kind: RuleKind
    evidence_level: EvidenceLevel
    mechanism: str
    conditions: tuple[Condition, ...]
    outcome: Mapping[str, Any]
    priority: int = 50
    message_key: str = ""
    sources: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    params: Mapping[str, Any] = field(default_factory=dict)

    def matches(self, facts: Mapping[str, Any]) -> bool:
        return all(condition.evaluate(facts) for condition in self.conditions)

    @property
    def can_recommend(self) -> bool:
        return self.evidence_level.can_recommend and self.kind is not RuleKind.MYTH

    @property
    def unmatched_reason_keys(self) -> tuple[str, ...]:
        return tuple(f"fact.{c.fact}" for c in self.conditions)


@dataclass(frozen=True)
class RuleMatch:
    rule: Rule
    facts_used: tuple[str, ...]

    @property
    def id(self) -> str:
        return self.rule.id
