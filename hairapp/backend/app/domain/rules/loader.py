"""Carga y validación estricta de packs de reglas.

Validación estricta significa: si una regla no declara etiqueta de evidencia,
mecanismo o condiciones válidas, **el pack entero no carga**. No hay valores por
defecto silenciosos. Un default convertiría un "no lo revisamos" en un
"consenso profesional" sin que nadie lo decidiera.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..evidence.language import ControlledLanguage
from ..evidence.language import errors as language_errors
from ..evidence.levels import EvidenceLevel
from .model import Condition, Operator, Rule, RuleKind

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[2] / "data" / "rules"

#: Etiquetas que exigen mecanismo explicado (docs/08-EVIDENCE-POLICY.md §4).
_MECHANISM_REQUIRED = {
    EvidenceLevel.SCIENTIFIC_EVIDENCE,
    EvidenceLevel.PROFESSIONAL_CONSENSUS,
}

#: Métodos de marca/autor que no pueden ser la única fuente de una regla.
#: Copiar un método único como verdad universal es el error concreto que B4
#: nos obliga a evitar; el Curly Girl Method es el caso canónico.
_SINGLE_METHOD_SOURCES = {
    "curly girl method",
    "cgm",
    "curly girl",
    "método curly girl",
    "max hydration method",
    "mhm",
}


class RulePackError(ValueError):
    """El pack de reglas es inválido. No se carga nada."""


@dataclass(frozen=True)
class RulePack:
    name: str
    version: int
    rules: tuple[Rule, ...]

    def by_id(self, rule_id: str) -> Rule:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        raise KeyError(rule_id)

    def of_kind(self, kind: RuleKind) -> tuple[Rule, ...]:
        return tuple(r for r in self.rules if r.kind is kind)

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)

    def __len__(self) -> int:
        return len(self.rules)


def load_rule_pack(path: Path, *, language: ControlledLanguage | None = None) -> RulePack:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise RulePackError(f"{path.name}: el pack debe ser un mapa en la raíz")

    name = raw.get("pack")
    version = raw.get("version")
    if not isinstance(name, str) or not isinstance(version, int):
        raise RulePackError(f"{path.name}: falta `pack` (str) o `version` (int)")

    rules_raw = raw.get("rules")
    if not isinstance(rules_raw, Sequence) or not rules_raw:
        raise RulePackError(f"{path.name}: `rules` debe ser una lista no vacía")

    rules = tuple(_parse_rule(item, path.name, index) for index, item in enumerate(rules_raw))
    _check_unique_ids(rules, path.name)
    if language is not None:
        _check_language(rules, path.name, language)
    return RulePack(name=name, version=version, rules=rules)


def load_all(
    directory: Path | None = None, *, language: ControlledLanguage | None = None
) -> tuple[Rule, ...]:
    target = directory or DEFAULT_RULES_DIR
    if not target.is_dir():
        raise RulePackError(f"no existe el directorio de reglas: {target}")
    packs = [load_rule_pack(p, language=language) for p in sorted(target.glob("*.yaml"))]
    if not packs:
        raise RulePackError(f"no se encontró ningún pack en {target}")
    rules = tuple(rule for pack in packs for rule in pack.rules)
    _check_unique_ids(rules, "global")
    return rules


def _parse_rule(item: Any, source_name: str, index: int) -> Rule:
    where = f"{source_name}[{index}]"
    if not isinstance(item, Mapping):
        raise RulePackError(f"{where}: cada regla debe ser un mapa")

    rule_id = item.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        raise RulePackError(f"{where}: falta `id`")
    where = f"{source_name}:{rule_id}"

    try:
        kind = RuleKind(item["kind"])
    except (KeyError, ValueError) as exc:
        raise RulePackError(f"{where}: `kind` ausente o desconocido") from exc

    if "evidence_level" not in item:
        raise RulePackError(
            f"{where}: falta `evidence_level`. Es obligatorio (B4): sin etiqueta "
            "la regla no puede cargarse, no se asume un valor por defecto."
        )
    try:
        level = EvidenceLevel(item["evidence_level"])
    except ValueError as exc:
        raise RulePackError(f"{where}: `evidence_level` desconocido: {item['evidence_level']!r}") from exc

    mechanism = item.get("mechanism", "")
    if level in _MECHANISM_REQUIRED and not str(mechanism).strip():
        raise RulePackError(
            f"{where}: la etiqueta `{level.value}` exige un `mechanism` explicado. "
            "Si no se puede explicar el mecanismo, la etiqueta máxima es "
            "`extended_anecdote`."
        )

    sources = tuple(str(s) for s in item.get("sources", ()))
    _check_sources(sources, where)

    conditions = tuple(
        _parse_condition(c, where, i) for i, c in enumerate(item.get("conditions", ()))
    )

    outcome = item.get("outcome")
    if kind is not RuleKind.MYTH and not isinstance(outcome, Mapping):
        raise RulePackError(f"{where}: falta `outcome` (mapa)")

    return Rule(
        id=rule_id,
        kind=kind,
        evidence_level=level,
        mechanism=str(mechanism).strip(),
        conditions=conditions,
        outcome=dict(outcome or {}),
        priority=int(item.get("priority", 50)),
        message_key=str(item.get("message_key", "")),
        sources=sources,
        tags=tuple(str(t) for t in item.get("tags", ())),
        conflicts_with=tuple(str(t) for t in item.get("conflicts_with", ())),
        params=dict(item.get("params", {})),
    )


def _parse_condition(raw: Any, where: str, index: int) -> Condition:
    if not isinstance(raw, Mapping):
        raise RulePackError(f"{where}: condición {index} debe ser un mapa")
    fact = raw.get("fact")
    if not isinstance(fact, str) or not fact:
        raise RulePackError(f"{where}: condición {index} sin `fact`")
    try:
        operator = Operator(raw["op"])
    except (KeyError, ValueError) as exc:
        raise RulePackError(f"{where}: condición {index} con `op` inválido") from exc

    needs_value = operator not in {
        Operator.IS_TRUE,
        Operator.IS_FALSE,
        Operator.EXISTS,
        Operator.MISSING,
    }
    if needs_value and "value" not in raw:
        raise RulePackError(f"{where}: condición {index} ({operator.value}) requiere `value`")

    return Condition(fact=fact, operator=operator, value=raw.get("value"))


def _check_unique_ids(rules: Iterable[Rule], where: str) -> None:
    seen: set[str] = set()
    for rule in rules:
        if rule.id in seen:
            raise RulePackError(f"{where}: id de regla duplicado: {rule.id}")
        seen.add(rule.id)


def _check_sources(sources: Sequence[str], where: str) -> None:
    if not sources:
        return
    lowered = {s.strip().lower() for s in sources}
    if lowered <= _SINGLE_METHOD_SOURCES:
        raise RulePackError(
            f"{where}: un método de marca o autor no puede ser la única fuente de "
            "una regla (B4). Describe el mecanismo subyacente y cita fuentes que "
            "lo sostengan."
        )


def _check_language(rules: Iterable[Rule], where: str, language: ControlledLanguage) -> None:
    findings = []
    for rule in rules:
        prescriptive = rule.kind in {RuleKind.ROUTINE_STEP, RuleKind.TECHNIQUE}
        findings += language.check(
            rule.mechanism, location=f"{where}:{rule.id}:mechanism", prescriptive=False
        )
        if rule.message_key:
            findings += language.check(
                rule.message_key, location=f"{where}:{rule.id}:message_key", prescriptive=prescriptive
            )
    hard = language_errors(findings)
    if hard:
        joined = "\n  ".join(str(f) for f in hard)
        raise RulePackError(f"{where}: lenguaje no permitido en el pack:\n  {joined}")
