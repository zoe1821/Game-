"""Glosario de lenguaje controlado, ejecutable (requisito B6).

No es un documento: es un checker. Se corre sobre los catálogos i18n, los packs
de reglas y el contenido educativo, y falla el build si aparece un término con
implicación médica. Ver docs/09-CONTROLLED-LANGUAGE.md y
docs/04-LEGAL-CHECKLIST.md §2.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import yaml

DEFAULT_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "data" / "controlled_language.yaml"


@dataclass(frozen=True)
class BlockedTerm:
    term: str
    replacement_key: str
    reason: str
    prescriptive_only: bool = False


@dataclass(frozen=True)
class ConditionalTerm:
    term: str
    condition: str


@dataclass(frozen=True)
class LanguageFinding:
    location: str
    term: str
    reason: str
    replacement_key: str
    severity: str  # "error" | "warning"
    excerpt: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.location}: «{self.term}» ({self.reason}) -> {self.replacement_key}"


def _normalise(text: str) -> str:
    """Minúsculas y sin acentos, para que «infección» y «infeccion» coincidan."""
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


class ControlledLanguage:
    def __init__(
        self,
        blocked: Iterable[BlockedTerm],
        conditional: Iterable[ConditionalTerm],
        referral_block_key: str,
    ) -> None:
        self.blocked = tuple(blocked)
        self.conditional = tuple(conditional)
        self.referral_block_key = referral_block_key
        self._patterns = [
            (term, re.compile(rf"(?<!\w){re.escape(_normalise(term.term))}(?!\w)"))
            for term in self.blocked
        ]
        self._conditional_patterns = [
            (term, re.compile(rf"(?<!\w){re.escape(_normalise(term.term))}(?!\w)"))
            for term in self.conditional
        ]

    @classmethod
    def load(cls, path: Path | None = None) -> "ControlledLanguage":
        source = path or DEFAULT_GLOSSARY_PATH
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
        blocked = [
            BlockedTerm(
                term=item["term"],
                replacement_key=item["replacement_key"],
                reason=item["reason"],
            )
            for item in raw.get("blocked", [])
        ]
        blocked += [
            BlockedTerm(
                term=item["term"],
                replacement_key=item["replacement_key"],
                reason=item["reason"],
                prescriptive_only=True,
            )
            for item in raw.get("prescriptive_blocked", [])
        ]
        conditional = [
            ConditionalTerm(term=item["term"], condition=item["condition"])
            for item in raw.get("conditional", [])
        ]
        return cls(blocked, conditional, raw["referral_block_key"])

    def check(self, text: str, *, location: str, prescriptive: bool = False) -> list[LanguageFinding]:
        """Revisa un texto. `prescriptive=True` activa además los imperativos."""
        haystack = _normalise(text)
        findings: list[LanguageFinding] = []
        for term, pattern in self._patterns:
            if term.prescriptive_only and not prescriptive:
                continue
            match = pattern.search(haystack)
            if match:
                findings.append(
                    LanguageFinding(
                        location=location,
                        term=term.term,
                        reason=term.reason,
                        replacement_key=term.replacement_key,
                        severity="error",
                        excerpt=_excerpt(text, match.start()),
                    )
                )
        for cond, pattern in self._conditional_patterns:
            match = pattern.search(haystack)
            if match:
                findings.append(
                    LanguageFinding(
                        location=location,
                        term=cond.term,
                        reason=f"conditional:{cond.condition}",
                        replacement_key="",
                        severity="warning",
                        excerpt=_excerpt(text, match.start()),
                    )
                )
        return findings

    def check_catalog(self, catalog: dict[str, object], *, location: str) -> list[LanguageFinding]:
        """Revisa un catálogo i18n anidado completo."""
        findings: list[LanguageFinding] = []
        for key, value in _walk(catalog):
            if not isinstance(value, str):
                continue
            prescriptive = key.startswith(("routine.", "recommendation.", "step."))
            findings.extend(
                self.check(value, location=f"{location}:{key}", prescriptive=prescriptive)
            )
        return findings

    @property
    def errors_only(self) -> "ControlledLanguage":
        return self


def _walk(node: object, prefix: str = "") -> Iterator[tuple[str, object]]:
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            yield from _walk(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{prefix}[{index}]")
    else:
        yield prefix, node


def _excerpt(text: str, index: int, radius: int = 30) -> str:
    start = max(0, index - radius)
    end = min(len(text), index + radius)
    return text[start:end].replace("\n", " ")


def errors(findings: Iterable[LanguageFinding]) -> list[LanguageFinding]:
    return [f for f in findings if f.severity == "error"]
