"""Estimación multi-señal de propiedades no observables directamente (A6).

Principio rector: **nunca una sola señal**. La porosidad en concreto se estima
combinando historial químico, comportamiento con agua, tiempo de secado y
observación visual — y explícitamente **no** con la prueba del vaso, que mide
sobre todo si la hebra tiene producto o aire atrapado (ver `myths.yaml`).

Cada estimación devuelve un `Measured` con la confianza ya penalizada por
conflicto entre señales y por calidad de la evidencia disponible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..common import Measured, Source, clamp
from ..confidence.engine import conflict_penalty, photo_quality_penalty
from .attributes import (
    Density,
    Elasticity,
    Porosity,
    ProcessingState,
    StrandDiameter,
)


@dataclass(frozen=True)
class Signal:
    """Una señal individual que apunta hacia un valor, con su peso."""

    name: str
    points_to: str
    weight: float
    detail: str | None = None


@dataclass
class PorosityInputs:
    """Todo lo que sabemos que puede informar la porosidad."""

    processing: ProcessingState | None = None
    months_since_last_chemical: float | None = None
    wets_slowly: bool | None = None
    """El agua tarda en penetrar: señal de porosidad baja."""
    dries_quickly: bool | None = None
    """Se seca muy rápido: señal de porosidad alta."""
    absorbs_product_fast: bool | None = None
    frizzes_in_humidity: bool | None = None
    feels_rough_when_dry: bool | None = None
    visible_cuticle_roughness: float | None = None
    """0-1, sólo si hubo métrica de imagen real. None si no hubo."""
    photo_quality: float | None = None
    heat_use_per_week: int | None = None


#: Pesos de cada señal. Suman más de 1 a propósito: el peso relativo importa,
#: no el absoluto, y se normaliza al agregar.
_POROSITY_WEIGHTS = {
    "processing": 0.30,
    "wets_slowly": 0.15,
    "dries_quickly": 0.20,
    "absorbs_product_fast": 0.12,
    "frizzes_in_humidity": 0.10,
    "feels_rough_when_dry": 0.12,
    "visible_cuticle_roughness": 0.18,
    "heat_use": 0.10,
}


def estimate_porosity(
    inputs: PorosityInputs, *, observed_at: date | None = None
) -> tuple[Measured[Porosity], list[Signal]]:
    """Estima porosidad combinando todas las señales disponibles.

    Devuelve también la lista de señales usadas, que es lo que alimenta el
    "¿por qué esto?" (A21): la persona ve exactamente qué se usó para decidir.
    """
    signals: list[Signal] = []

    if inputs.processing is not None:
        if inputs.processing in {ProcessingState.BLEACHED, ProcessingState.HIGHLIGHTED}:
            signals.append(Signal("processing", "high", _POROSITY_WEIGHTS["processing"], "bleached"))
        elif inputs.processing in {
            ProcessingState.COLOURED,
            ProcessingState.RELAXED,
            ProcessingState.PERMED,
            ProcessingState.CHEMICALLY_STRAIGHTENED,
        }:
            signals.append(Signal("processing", "high", _POROSITY_WEIGHTS["processing"] * 0.7))
        elif inputs.processing is ProcessingState.TRANSITIONING:
            signals.append(Signal("processing", "mixed", _POROSITY_WEIGHTS["processing"]))
        elif inputs.processing is ProcessingState.VIRGIN:
            signals.append(Signal("processing", "low", _POROSITY_WEIGHTS["processing"] * 0.6))

    if inputs.wets_slowly is not None:
        signals.append(
            Signal("wets_slowly", "low" if inputs.wets_slowly else "high", _POROSITY_WEIGHTS["wets_slowly"])
        )
    if inputs.dries_quickly is not None:
        signals.append(
            Signal("dries_quickly", "high" if inputs.dries_quickly else "low", _POROSITY_WEIGHTS["dries_quickly"])
        )
    if inputs.absorbs_product_fast is not None:
        signals.append(
            Signal(
                "absorbs_product_fast",
                "high" if inputs.absorbs_product_fast else "low",
                _POROSITY_WEIGHTS["absorbs_product_fast"],
            )
        )
    if inputs.frizzes_in_humidity is not None and inputs.frizzes_in_humidity:
        signals.append(Signal("frizzes_in_humidity", "high", _POROSITY_WEIGHTS["frizzes_in_humidity"]))
    if inputs.feels_rough_when_dry is not None and inputs.feels_rough_when_dry:
        signals.append(Signal("feels_rough_when_dry", "high", _POROSITY_WEIGHTS["feels_rough_when_dry"]))
    if inputs.visible_cuticle_roughness is not None:
        weight = _POROSITY_WEIGHTS["visible_cuticle_roughness"]
        if inputs.photo_quality is not None:
            weight *= photo_quality_penalty(inputs.photo_quality)
        signals.append(
            Signal(
                "visible_cuticle_roughness",
                "high" if inputs.visible_cuticle_roughness > 0.55 else "low",
                weight,
            )
        )
    if inputs.heat_use_per_week is not None and inputs.heat_use_per_week >= 3:
        signals.append(Signal("heat_use", "high", _POROSITY_WEIGHTS["heat_use"]))

    if not signals:
        # Sin ninguna señal no se estima. Devolver "media por defecto" con
        # confianza baja sería inventar; el sistema prefiere decir que no sabe.
        return (
            Measured(
                value=Porosity.MEDIUM,
                source=Source.DEFAULT,
                confidence=0.0,
                observed_at=observed_at,
                notes="no_signals_available",
            ),
            signals,
        )

    scores: dict[str, float] = {"low": 0.0, "high": 0.0, "mixed": 0.0}
    for signal in signals:
        scores[signal.points_to] += signal.weight

    total = sum(scores.values())
    winner = max(scores, key=lambda k: scores[k])
    margin = scores[winner] / total if total else 0.0

    # Empate real -> porosidad media, que es una conclusión legítima, no un relleno.
    if margin < 0.5 and scores["mixed"] < scores[winner]:
        value = Porosity.MEDIUM
        margin = 1.0 - abs(scores["high"] - scores["low"]) / total if total else 0.0
    else:
        value = {"low": Porosity.LOW, "high": Porosity.HIGH, "mixed": Porosity.MIXED}[winner]

    conflicting = sum(1 for s in signals if s.points_to != winner)
    coverage = clamp(total / sum(_POROSITY_WEIGHTS.values()))
    confidence = clamp(margin * coverage * conflict_penalty(conflicting))
    confidence = min(confidence, Source.INFERRED.confidence_ceiling)

    return (
        Measured(value=value, source=Source.INFERRED, confidence=confidence, observed_at=observed_at),
        signals,
    )


@dataclass
class DensityInputs:
    """Señales de densidad. La observación directa gana sobre las indirectas."""

    ponytail_circumference_cm: float | None = None
    scalp_visible_when_parted: bool | None = None
    strands_per_cm2: float | None = None
    user_reported: Density | None = None


def estimate_density(inputs: DensityInputs, *, observed_at: date | None = None) -> Measured[Density]:
    """Estima densidad por zona.

    La circunferencia de coleta es la medición casera más reproducible que
    existe para esto; los rangos son orientativos y varían con la longitud, así
    que la confianza nunca es alta por sí sola.
    """
    if inputs.user_reported is not None:
        return Measured(inputs.user_reported, Source.USER, 1.0, observed_at)

    if inputs.strands_per_cm2 is not None:
        if inputs.strands_per_cm2 < 100:
            value = Density.LOW
        elif inputs.strands_per_cm2 < 200:
            value = Density.MEDIUM
        else:
            value = Density.HIGH
        return Measured(value, Source.INFERRED, 0.7, observed_at)

    if inputs.ponytail_circumference_cm is not None:
        circumference = inputs.ponytail_circumference_cm
        if circumference < 5.0:
            value = Density.LOW
        elif circumference < 10.0:
            value = Density.MEDIUM
        else:
            value = Density.HIGH
        confidence = 0.55
        if inputs.scalp_visible_when_parted is not None:
            agrees = (inputs.scalp_visible_when_parted and value is Density.LOW) or (
                not inputs.scalp_visible_when_parted and value is not Density.LOW
            )
            confidence = 0.68 if agrees else 0.35
        return Measured(value, Source.INFERRED, confidence, observed_at)

    if inputs.scalp_visible_when_parted is not None:
        value = Density.LOW if inputs.scalp_visible_when_parted else Density.MEDIUM
        return Measured(value, Source.INFERRED, 0.35, observed_at)

    return Measured(Density.MEDIUM, Source.DEFAULT, 0.0, observed_at, notes="no_signals_available")


@dataclass
class ElasticityTest:
    """Prueba guiada de elasticidad (A6).

    Se hace sobre una hebra ya desprendida, en húmedo, y se registra el
    estiramiento y si recupera. Es una prueba casera: informativa, no medición.
    """

    stretch_ratio: float | None = None
    returns_to_length: bool | None = None
    snaps_immediately: bool | None = None
    feels_gummy: bool | None = None


def estimate_elasticity(test: ElasticityTest, *, observed_at: date | None = None) -> Measured[Elasticity]:
    if test.snaps_immediately:
        return Measured(Elasticity.LOW, Source.INFERRED, 0.7, observed_at)
    if test.feels_gummy or (test.stretch_ratio is not None and test.stretch_ratio >= 1.5 and test.returns_to_length is False):
        return Measured(Elasticity.EXCESSIVE, Source.INFERRED, 0.7, observed_at)
    if test.stretch_ratio is None:
        return Measured(Elasticity.NORMAL, Source.DEFAULT, 0.0, observed_at, notes="no_signals_available")
    if test.stretch_ratio < 1.15:
        return Measured(Elasticity.LOW, Source.INFERRED, 0.55, observed_at)
    if test.returns_to_length:
        return Measured(Elasticity.NORMAL, Source.INFERRED, 0.65, observed_at)
    return Measured(Elasticity.EXCESSIVE, Source.INFERRED, 0.6, observed_at)


@dataclass
class StrandDiameterInputs:
    compared_to_thread: str | None = None
    """`thinner`, `similar` o `thicker` que un hilo de coser."""
    barely_felt_between_fingers: bool | None = None
    measured_microns: float | None = None


def estimate_strand_diameter(
    inputs: StrandDiameterInputs, *, observed_at: date | None = None
) -> Measured[StrandDiameter]:
    if inputs.measured_microns is not None:
        if inputs.measured_microns < 60:
            value = StrandDiameter.FINE
        elif inputs.measured_microns < 90:
            value = StrandDiameter.MEDIUM
        else:
            value = StrandDiameter.COARSE
        return Measured(value, Source.INFERRED, 0.8, observed_at)

    mapping = {
        "thinner": StrandDiameter.FINE,
        "similar": StrandDiameter.MEDIUM,
        "thicker": StrandDiameter.COARSE,
    }
    if inputs.compared_to_thread in mapping:
        value = mapping[inputs.compared_to_thread]
        confidence = 0.6
        if inputs.barely_felt_between_fingers is not None:
            agrees = inputs.barely_felt_between_fingers == (value is StrandDiameter.FINE)
            confidence = 0.7 if agrees else 0.4
        return Measured(value, Source.INFERRED, confidence, observed_at)

    if inputs.barely_felt_between_fingers is not None:
        value = StrandDiameter.FINE if inputs.barely_felt_between_fingers else StrandDiameter.MEDIUM
        return Measured(value, Source.INFERRED, 0.35, observed_at)

    return Measured(StrandDiameter.MEDIUM, Source.DEFAULT, 0.0, observed_at, notes="no_signals_available")
