"""Hair Digital Twin (A24).

**Qué es:** una representación estructurada y actualizable del comportamiento
observado del cabello de una persona concreta.

**Qué no es:** una simulación física de hebras. No modelamos mecánica de fibras
ni renderizamos pelo. Eso sería vistoso y falso, y la regla del proyecto es
elegir lo real y limitado.

El twin responde preguntas del tipo "¿qué probablemente ocurre si...?" a partir
de lo que ya pasó, **siempre** mostrando en qué se basa y cuánta incertidumbre
hay. Cuando no tiene base, lo dice: no proyecta.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..common import clamp
from ..experiments.engine import ExperimentReading
from ..learning.journal import Finding, JournalEntry, Strength


class TraitKey(enum.Enum):
    """Los rasgos de comportamiento que el twin sigue.

    Son rasgos **observables en el uso diario**, no propiedades de laboratorio.
    Cada uno responde a una pregunta que la persona se hace de verdad.
    """

    HUMIDITY_SENSITIVITY = "humidity_sensitivity"
    """Cuánto empeora con punto de rocío alto."""
    PROTEIN_TOLERANCE = "protein_tolerance"
    """Cuánta proteína admite antes de notarse rígido."""
    STYLE_LONGEVITY_DAYS = "style_longevity_days"
    """Cuántos días aguanta el peinado en estado aceptable."""
    PRODUCT_LOAD_TOLERANCE = "product_load_tolerance"
    """Cuánto producto admite antes de apelmazarse."""
    DRYING_SPEED = "drying_speed"
    HEAT_SENSITIVITY = "heat_sensitivity"
    BUILDUP_SPEED = "buildup_speed"
    REFRESH_RESPONSE = "refresh_response"
    """Si un refresh entre lavados le funciona o empeora el resultado."""

    @property
    def label_key(self) -> str:
        return f"twin.trait.{self.value}"


@dataclass(frozen=True)
class Trait:
    """Un rasgo con su valor, su respaldo y su incertidumbre."""

    key: TraitKey
    value: float
    """Normalizado 0-1, salvo `STYLE_LONGEVITY_DAYS`, que va en días."""
    confidence: float
    sample_size: int
    based_on: tuple[str, ...]
    """Ids de las observaciones que lo sostienen: entradas, experimentos."""
    last_updated: date | None = None
    is_controlled: bool = False
    """True si al menos parte del respaldo viene de experimentos controlados."""

    @property
    def is_known(self) -> bool:
        return self.confidence > 0.0 and self.sample_size > 0

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key.value,
            "value": round(self.value, 3),
            "confidence": round(self.confidence, 3),
            "sample_size": self.sample_size,
            "based_on": list(self.based_on),
            "is_controlled": self.is_controlled,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass(frozen=True)
class DigitalTwin:
    profile_id: str
    traits: Mapping[TraitKey, Trait]
    entry_count: int
    created_at: date | None = None

    def trait(self, key: TraitKey) -> Trait | None:
        found = self.traits.get(key)
        return found if found and found.is_known else None

    @property
    def known_traits(self) -> tuple[Trait, ...]:
        return tuple(t for t in self.traits.values() if t.is_known)

    @property
    def completeness(self) -> float:
        return len(self.known_traits) / len(TraitKey)

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "entry_count": self.entry_count,
            "completeness": round(self.completeness, 2),
            "traits": [t.as_dict() for t in self.traits.values()],
        }


def build_twin(
    *,
    profile_id: str,
    entries: Sequence[JournalEntry],
    findings: Sequence[Finding] = (),
    experiment_readings: Sequence[ExperimentReading] = (),
    today: date | None = None,
) -> DigitalTwin:
    """Construye el twin a partir de lo observado.

    Los rasgos que no se puedan derivar quedan con confianza 0 y se muestran
    como "todavía no lo sé", que es información útil: dice qué registrar.
    """
    traits: dict[TraitKey, Trait] = {}

    traits[TraitKey.STYLE_LONGEVITY_DAYS] = _longevity(entries, today)
    traits[TraitKey.HUMIDITY_SENSITIVITY] = _humidity_sensitivity(entries, today)
    traits[TraitKey.PRODUCT_LOAD_TOLERANCE] = _product_load(entries, today)
    traits[TraitKey.REFRESH_RESPONSE] = _from_findings(
        TraitKey.REFRESH_RESPONSE, findings, "refresh", today
    )

    for key in TraitKey:
        traits.setdefault(key, _unknown(key))

    traits = _apply_experiments(traits, experiment_readings, today)

    return DigitalTwin(
        profile_id=profile_id,
        traits=traits,
        entry_count=len(entries),
        created_at=today,
    )


def _unknown(key: TraitKey) -> Trait:
    return Trait(key=key, value=0.0, confidence=0.0, sample_size=0, based_on=())


def _longevity(entries: Sequence[JournalEntry], today: date | None) -> Trait:
    values = [e.longevity_days for e in entries if e.rating_day1 is not None]
    if len(values) < 3:
        return _unknown(TraitKey.STYLE_LONGEVITY_DAYS)
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    # Mucha dispersión significa que el rasgo no es estable: confianza baja
    # aunque haya muchos registros. Un promedio de 2,5 días entre valores de 1 y
    # 4 no describe nada.
    stability = clamp(1.0 - spread / 4.0, low=0.2)
    confidence = clamp((1.0 - 2.718 ** (-len(values) / 6.0)) * stability, high=0.85)
    return Trait(
        key=TraitKey.STYLE_LONGEVITY_DAYS,
        value=mean,
        confidence=confidence,
        sample_size=len(values),
        based_on=tuple(e.id for e in entries[-8:]),
        last_updated=today,
    )


def _humidity_sensitivity(entries: Sequence[JournalEntry], today: date | None) -> Trait:
    """Correlación entre punto de rocío y resultado.

    Necesita variación real de clima: si todos los registros son del mismo
    punto de rocío, no hay nada que correlacionar y se declara desconocido.
    """
    pairs = [
        (e.dew_point_c, e.mean_rating)
        for e in entries
        if e.dew_point_c is not None and e.mean_rating is not None
    ]
    if len(pairs) < 5:
        return _unknown(TraitKey.HUMIDITY_SENSITIVITY)

    dews = [p[0] for p in pairs]
    if max(dews) - min(dews) < 6.0:
        # Sin variación de clima no se puede saber. Decirlo es la respuesta.
        return _unknown(TraitKey.HUMIDITY_SENSITIVITY)

    correlation = _pearson([p[0] for p in pairs], [p[1] for p in pairs])
    # Correlación negativa = peor con más humedad = más sensible.
    sensitivity = clamp((-correlation + 1.0) / 2.0)
    confidence = clamp(abs(correlation) * (1.0 - 2.718 ** (-len(pairs) / 8.0)), high=0.8)
    return Trait(
        key=TraitKey.HUMIDITY_SENSITIVITY,
        value=sensitivity,
        confidence=confidence,
        sample_size=len(pairs),
        based_on=tuple(e.id for e in entries[-8:]),
        last_updated=today,
    )


def _product_load(entries: Sequence[JournalEntry], today: date | None) -> Trait:
    pairs = [
        (sum(e.amounts_ml.values()), e.mean_rating)
        for e in entries
        if e.amounts_ml and e.mean_rating is not None
    ]
    if len(pairs) < 5:
        return _unknown(TraitKey.PRODUCT_LOAD_TOLERANCE)
    loads = [p[0] for p in pairs]
    if max(loads) - min(loads) < 2.0:
        return _unknown(TraitKey.PRODUCT_LOAD_TOLERANCE)
    correlation = _pearson(loads, [p[1] for p in pairs])
    tolerance = clamp((correlation + 1.0) / 2.0)
    confidence = clamp(abs(correlation) * (1.0 - 2.718 ** (-len(pairs) / 8.0)), high=0.8)
    return Trait(
        key=TraitKey.PRODUCT_LOAD_TOLERANCE,
        value=tolerance,
        confidence=confidence,
        sample_size=len(pairs),
        based_on=tuple(e.id for e in entries[-8:]),
        last_updated=today,
    )


def _from_findings(
    key: TraitKey, findings: Sequence[Finding], needle: str, today: date | None
) -> Trait:
    relevant = [f for f in findings if needle in f.subject.lower()]
    if not relevant:
        return _unknown(key)
    best = max(relevant, key=lambda f: abs(f.effect_size))
    if best.strength is Strength.INSUFFICIENT_DATA:
        return _unknown(key)
    return Trait(
        key=key,
        value=clamp((best.effect_size + 3.0) / 6.0),
        confidence=best.explanation.personal_confidence,
        sample_size=best.with_n + best.without_n,
        based_on=(best.subject,),
        last_updated=today,
    )


def _apply_experiments(
    traits: dict[TraitKey, Trait],
    readings: Sequence[ExperimentReading],
    today: date | None,
) -> dict[TraitKey, Trait]:
    """Marca como controlados los rasgos respaldados por un experimento.

    No sobrescribe valores: un experimento sobre "crema sí o no" no mide
    directamente ningún rasgo del twin. Lo que sí hace es subir la confianza de
    lo que el experimento tocó, y dejar constancia de que hubo control.
    """
    conclusive = [r for r in readings if r.is_conclusive]
    if not conclusive:
        return traits

    updated = dict(traits)
    for key, trait in traits.items():
        if not trait.is_known:
            continue
        updated[key] = Trait(
            key=trait.key,
            value=trait.value,
            confidence=clamp(trait.confidence * 1.1, high=0.9),
            sample_size=trait.sample_size,
            based_on=trait.based_on + tuple(r.experiment_id for r in conclusive),
            last_updated=today,
            is_controlled=True,
        )
    return updated


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / (var_x**0.5 * var_y**0.5)
