"""Aprendizaje a partir del diario de wash day (A13).

La honestidad estadística es el producto aquí. Un motor que dice "el gel X te
funciona mejor" con tres registros y sin controlar el clima no está aprendiendo:
está confirmando sesgos. Este módulo:

  - distingue correlación de causalidad de forma explícita,
  - muestra siempre el tamaño de muestra,
  - declara qué variables **no** estaban controladas,
  - y se niega a concluir cuando la muestra no da.
"""

from __future__ import annotations

import enum
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from ..common import Explanation, clamp


class ResultRating(enum.Enum):
    """Cómo salió el día. Escala corta a propósito: una escala de 1-10 sugiere
    una precisión que nadie tiene al valorar su propio pelo."""

    BAD = 1
    MEH = 2
    GOOD = 3
    GREAT = 4


@dataclass(frozen=True)
class JournalEntry:
    """Un wash day registrado, con su contexto."""

    id: str
    date: date
    product_ids: tuple[str, ...] = ()
    technique_ids: tuple[str, ...] = ()
    dew_point_c: float | None = None
    water_hardness_ppm: float | None = None
    amounts_ml: Mapping[str, float] = field(default_factory=dict)
    rating_day1: ResultRating | None = None
    rating_day2: ResultRating | None = None
    rating_day3: ResultRating | None = None
    rating_day4_plus: ResultRating | None = None
    notes: str | None = None
    experiment_arm_id: str | None = None
    """Si viene de un experimento controlado, pesa más (A25)."""

    @property
    def is_controlled(self) -> bool:
        return self.experiment_arm_id is not None

    @property
    def mean_rating(self) -> float | None:
        ratings = [
            r.value
            for r in (self.rating_day1, self.rating_day2, self.rating_day3, self.rating_day4_plus)
            if r is not None
        ]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)

    @property
    def longevity_days(self) -> int:
        """Cuántos días aguantó en estado aceptable."""
        days = 0
        for rating in (self.rating_day1, self.rating_day2, self.rating_day3, self.rating_day4_plus):
            if rating is None or rating.value < ResultRating.GOOD.value:
                break
            days += 1
        return days


class Strength(enum.Enum):
    INSUFFICIENT_DATA = "insufficient_data"
    SUGGESTIVE = "suggestive"
    CONSISTENT = "consistent"
    STRONG = "strong"

    @property
    def label_key(self) -> str:
        return f"learning.strength.{self.value}"


#: Mínimos por debajo de los cuales no se concluye nada. Son deliberadamente
#: conservadores: preferimos decir "todavía no sé" a inventar un patrón.
MIN_ENTRIES_PER_SIDE = 3
MIN_TOTAL_ENTRIES = 6


@dataclass(frozen=True)
class Finding:
    """Un patrón observado en el historial. Nunca se presenta como causa."""

    subject: str
    """Qué se observó: un id de producto, de técnica, o un factor de contexto."""
    kind: str  # "product" | "technique" | "context"
    with_mean: float
    without_mean: float
    with_n: int
    without_n: int
    strength: Strength
    effect_size: float
    """Diferencia de medias en unidades de desviación típica agrupada."""
    uncontrolled_variables: tuple[str, ...]
    explanation: Explanation

    @property
    def difference(self) -> float:
        return self.with_mean - self.without_mean

    @property
    def is_actionable(self) -> bool:
        return self.strength in {Strength.CONSISTENT, Strength.STRONG}

    def as_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "with_mean": round(self.with_mean, 2),
            "without_mean": round(self.without_mean, 2),
            "with_n": self.with_n,
            "without_n": self.without_n,
            "sample_size": self.with_n + self.without_n,
            "difference": round(self.difference, 2),
            "effect_size": round(self.effect_size, 2),
            "strength": self.strength.value,
            "is_actionable": self.is_actionable,
            "uncontrolled_variables": list(self.uncontrolled_variables),
            "explanation": self.explanation.as_dict(),
        }


def analyse_journal(
    entries: Sequence[JournalEntry],
    *,
    min_entries: int = MIN_TOTAL_ENTRIES,
) -> list[Finding]:
    """Busca patrones en el historial, sin afirmar causalidad.

    Devuelve lista vacía cuando no hay datos suficientes. Esa lista vacía es
    una respuesta correcta, no un fallo: la app la muestra como "todavía estoy
    aprendiendo de ti" (B2).
    """
    usable = [e for e in entries if e.mean_rating is not None]
    if len(usable) < min_entries:
        return []

    findings: list[Finding] = []
    for subject, kind in _subjects(usable):
        finding = _compare(usable, subject, kind)
        if finding is not None:
            findings.append(finding)

    findings.sort(key=lambda f: (f.strength.value, abs(f.effect_size)), reverse=True)
    return findings


def _subjects(entries: Sequence[JournalEntry]) -> list[tuple[str, str]]:
    products = {p for e in entries for p in e.product_ids}
    techniques = {t for e in entries for t in e.technique_ids}
    return [(p, "product") for p in sorted(products)] + [(t, "technique") for t in sorted(techniques)]


def _compare(entries: Sequence[JournalEntry], subject: str, kind: str) -> Finding | None:
    def used(entry: JournalEntry) -> bool:
        pool = entry.product_ids if kind == "product" else entry.technique_ids
        return subject in pool

    with_entries = [e for e in entries if used(e)]
    without_entries = [e for e in entries if not used(e)]

    if len(with_entries) < MIN_ENTRIES_PER_SIDE or len(without_entries) < MIN_ENTRIES_PER_SIDE:
        return None

    with_values = [e.mean_rating for e in with_entries if e.mean_rating is not None]
    without_values = [e.mean_rating for e in without_entries if e.mean_rating is not None]

    with_mean = _mean(with_values)
    without_mean = _mean(without_values)
    effect = _cohens_d(with_values, without_values)

    uncontrolled = _uncontrolled(with_entries, without_entries)
    controlled_share = sum(1 for e in with_entries + without_entries if e.is_controlled)
    strength = _strength(
        n_with=len(with_entries),
        n_without=len(without_entries),
        effect=effect,
        uncontrolled=uncontrolled,
        controlled_entries=controlled_share,
    )

    explanation = Explanation(
        summary_key="learning.finding.why",
        inputs_used=("input.journal",),
        observations=(
            f"with_n={len(with_entries)}",
            f"without_n={len(without_entries)}",
            f"effect_size={effect:.2f}",
        ),
        evidence_level="extended_anecdote",
        # Un patrón del historial propio no es evidencia general: la confianza
        # de evidencia es baja por definición, y la personal es la que sube.
        evidence_confidence=0.45,
        personal_confidence=_personal_confidence(len(with_entries) + len(without_entries), effect),
        sample_size=len(with_entries) + len(without_entries),
        uncertainty_keys=(
            "uncertainty.correlation_not_causation",
            *(f"uncertainty.uncontrolled.{v}" for v in uncontrolled),
        ),
        alternatives=("learning.alternative.run_a_controlled_experiment",),
        params={"subject": subject, "kind": kind},
    )

    return Finding(
        subject=subject,
        kind=kind,
        with_mean=with_mean,
        without_mean=without_mean,
        with_n=len(with_entries),
        without_n=len(without_entries),
        strength=strength,
        effect_size=effect,
        uncontrolled_variables=uncontrolled,
        explanation=explanation,
    )


def _uncontrolled(
    with_entries: Sequence[JournalEntry], without_entries: Sequence[JournalEntry]
) -> tuple[str, ...]:
    """Detecta variables que difieren sistemáticamente entre los dos grupos.

    Si los días en que usaste el gel A fueron además días más húmedos, la
    comparación no aísla el gel. Decirlo es la diferencia entre una herramienta
    y un horóscopo.
    """
    uncontrolled: list[str] = []

    with_dew = [e.dew_point_c for e in with_entries if e.dew_point_c is not None]
    without_dew = [e.dew_point_c for e in without_entries if e.dew_point_c is not None]
    if with_dew and without_dew and abs(_mean(with_dew) - _mean(without_dew)) > 4.0:
        uncontrolled.append("dew_point")
    if not with_dew or not without_dew:
        uncontrolled.append("dew_point_missing")

    with_products = {p for e in with_entries for p in e.product_ids}
    without_products = {p for e in without_entries for p in e.product_ids}
    if len(with_products ^ without_products) > 2:
        uncontrolled.append("other_products")

    with_techniques = {t for e in with_entries for t in e.technique_ids}
    without_techniques = {t for e in without_entries for t in e.technique_ids}
    if with_techniques ^ without_techniques:
        uncontrolled.append("techniques")

    return tuple(dict.fromkeys(uncontrolled))


#: Variables cuya diferencia sistemática entre los dos grupos **compite** con la
#: explicación que se está evaluando. No es lo mismo que un dato ausente: si el
#: gel A se usó siempre en días secos, la comparación no aísla el gel, y ningún
#: tamaño de muestra arregla eso.
_CONFOUNDS = frozenset({"dew_point", "other_products"})

_STRENGTH_LADDER: tuple[Strength, ...] = (
    Strength.INSUFFICIENT_DATA,
    Strength.SUGGESTIVE,
    Strength.CONSISTENT,
    Strength.STRONG,
)


def _strength(
    *,
    n_with: int,
    n_without: int,
    effect: float,
    uncontrolled: Sequence[str],
    controlled_entries: int,
) -> Strength:
    total = n_with + n_without
    magnitude = abs(effect)
    uncontrolled_count = len(uncontrolled)

    if total < MIN_TOTAL_ENTRIES or magnitude < 0.2:
        return Strength.INSUFFICIENT_DATA

    if total >= 16 and magnitude >= 0.8 and uncontrolled_count <= 1 or controlled_entries >= 6 and magnitude >= 0.5:
        base = Strength.STRONG
    elif total >= 10 and magnitude >= 0.5 and uncontrolled_count <= 2:
        base = Strength.CONSISTENT
    else:
        base = Strength.SUGGESTIVE

    confounds = len(_CONFOUNDS & set(uncontrolled))
    if confounds and controlled_entries < 6:
        # Cada variable que compite baja un escalón. Un experimento controlado
        # sí neutraliza el problema, porque ahí las variables se fijaron a
        # propósito (A25); una observación suelta no.
        index = max(0, _STRENGTH_LADDER.index(base) - confounds)
        return _STRENGTH_LADDER[index]
    return base


def _personal_confidence(sample_size: int, effect: float) -> float:
    size_factor = 1.0 - math.exp(-sample_size / 8.0)
    effect_factor = clamp(abs(effect) / 1.2)
    return clamp(size_factor * effect_factor)


#: Tope del tamaño del efecto. Por encima de 3 desviaciones típicas la cifra
#: exacta deja de aportar y solo introduce ruido en la ordenación.
_MAX_EFFECT_SIZE = 3.0


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Tamaño del efecto. Una diferencia de medias sin esto no dice nada:
    0.3 puntos de diferencia puede ser enorme o ruido según la dispersión."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    mean_a, mean_b = _mean(a), _mean(b)
    var_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    if pooled == 0:
        # Dispersión nula en ambos grupos. Si además las medias coinciden no hay
        # efecto; si difieren, la separación es total y `d` tendería a infinito,
        # así que se acota en un valor alto en vez de devolver 0, que sería
        # justo la conclusión contraria a la que muestran los datos.
        difference = mean_a - mean_b
        if difference == 0:
            return 0.0
        return math.copysign(_MAX_EFFECT_SIZE, difference)
    return clamp((mean_a - mean_b) / pooled, low=-_MAX_EFFECT_SIZE, high=_MAX_EFFECT_SIZE)
