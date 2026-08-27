"""Proyecciones del digital twin: "¿qué pasa probablemente si...?" (A24).

Regla dura: **una proyección sin base histórica no se emite.** Si el twin no
conoce el rasgo relevante, la respuesta es "todavía no lo sé, y esto es lo que
tendría que registrar para saberlo", no una estimación inventada con un
porcentaje bonito al lado.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ..common import Explanation, clamp
from .model import DigitalTwin, TraitKey


class Scenario(enum.Enum):
    HIGHER_HUMIDITY = "higher_humidity"
    LOWER_HUMIDITY = "lower_humidity"
    MORE_PRODUCT = "more_product"
    LESS_PRODUCT = "less_product"
    ADD_PROTEIN = "add_protein"
    SKIP_GEL = "skip_gel"
    STRETCH_WASH_DAY = "stretch_wash_day"
    REFRESH_INSTEAD_OF_WASH = "refresh_instead_of_wash"

    @property
    def label_key(self) -> str:
        return f"twin.scenario.{self.value}"


#: Qué rasgo necesita cada escenario para poder proyectarse.
_REQUIRED_TRAIT: dict[Scenario, TraitKey] = {
    Scenario.HIGHER_HUMIDITY: TraitKey.HUMIDITY_SENSITIVITY,
    Scenario.LOWER_HUMIDITY: TraitKey.HUMIDITY_SENSITIVITY,
    Scenario.MORE_PRODUCT: TraitKey.PRODUCT_LOAD_TOLERANCE,
    Scenario.LESS_PRODUCT: TraitKey.PRODUCT_LOAD_TOLERANCE,
    Scenario.ADD_PROTEIN: TraitKey.PROTEIN_TOLERANCE,
    Scenario.SKIP_GEL: TraitKey.STYLE_LONGEVITY_DAYS,
    Scenario.STRETCH_WASH_DAY: TraitKey.STYLE_LONGEVITY_DAYS,
    Scenario.REFRESH_INSTEAD_OF_WASH: TraitKey.REFRESH_RESPONSE,
}


class Direction(enum.Enum):
    LIKELY_BETTER = "likely_better"
    LIKELY_WORSE = "likely_worse"
    LIKELY_SIMILAR = "likely_similar"
    UNKNOWN = "unknown"

    @property
    def label_key(self) -> str:
        return f"twin.direction.{self.value}"


@dataclass(frozen=True)
class Projection:
    scenario: Scenario
    direction: Direction
    magnitude: float
    """0-1. Cuánto se espera que cambie, no cuánto de seguro estamos."""
    confidence: float
    sample_size: int
    can_project: bool
    missing_data_keys: tuple[str, ...]
    """Qué haría falta registrar para poder responder. Es la salida útil
    cuando no se puede proyectar."""
    explanation: Explanation

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario.value,
            "direction": self.direction.value,
            "magnitude": round(self.magnitude, 2),
            "confidence": round(self.confidence, 2),
            "sample_size": self.sample_size,
            "can_project": self.can_project,
            "missing_data_keys": list(self.missing_data_keys),
            "explanation": self.explanation.as_dict(),
        }


#: Qué hace falta registrar para desbloquear cada rasgo. Convierte un "no sé"
#: en una instrucción concreta.
_UNLOCK_HINTS: dict[TraitKey, tuple[str, ...]] = {
    TraitKey.HUMIDITY_SENSITIVITY: (
        "twin.unlock.log_five_wash_days",
        "twin.unlock.log_across_different_weather",
    ),
    TraitKey.PRODUCT_LOAD_TOLERANCE: (
        "twin.unlock.log_amounts_used",
        "twin.unlock.vary_the_amount_deliberately",
    ),
    TraitKey.PROTEIN_TOLERANCE: (
        "twin.unlock.run_protein_experiment",
    ),
    TraitKey.STYLE_LONGEVITY_DAYS: (
        "twin.unlock.rate_days_2_and_3",
    ),
    TraitKey.REFRESH_RESPONSE: (
        "twin.unlock.try_a_refresh_and_log_it",
    ),
}


def project(twin: DigitalTwin, scenario: Scenario) -> Projection:
    required = _REQUIRED_TRAIT[scenario]
    trait = twin.trait(required)

    if trait is None:
        return Projection(
            scenario=scenario,
            direction=Direction.UNKNOWN,
            magnitude=0.0,
            confidence=0.0,
            sample_size=0,
            can_project=False,
            missing_data_keys=_UNLOCK_HINTS.get(required, ()),
            explanation=Explanation(
                summary_key="twin.projection.not_enough_history",
                inputs_used=("input.digital_twin",),
                observations=(f"missing_trait={required.value}",),
                evidence_level="extended_anecdote",
                evidence_confidence=0.0,
                personal_confidence=0.0,
                sample_size=twin.entry_count,
                uncertainty_keys=("uncertainty.no_basis_for_projection",),
                alternatives=_UNLOCK_HINTS.get(required, ()),
                params={"required_trait": required.value},
            ),
        )

    direction, magnitude = _direction_for(scenario, trait.value)

    return Projection(
        scenario=scenario,
        direction=direction,
        magnitude=magnitude,
        confidence=trait.confidence,
        sample_size=trait.sample_size,
        can_project=True,
        missing_data_keys=(),
        explanation=Explanation(
            summary_key="twin.projection.based_on_your_history",
            inputs_used=("input.digital_twin", "input.journal"),
            observations=(
                f"trait={required.value}",
                f"trait_value={trait.value:.2f}",
                f"n={trait.sample_size}",
            ),
            evidence_level="extended_anecdote",
            # Una proyección del propio historial no es evidencia general.
            evidence_confidence=0.45,
            personal_confidence=trait.confidence,
            sample_size=trait.sample_size,
            uncertainty_keys=(
                "uncertainty.projection_is_not_a_prediction",
                *(() if trait.is_controlled else ("uncertainty.uncontrolled_observations",)),
            ),
            alternatives=("twin.alternative.test_it_as_an_experiment",),
            params={
                "based_on": list(trait.based_on),
                "is_controlled": trait.is_controlled,
            },
        ),
    )


def _direction_for(scenario: Scenario, trait_value: float) -> tuple[Direction, float]:
    """Traduce el valor del rasgo a una dirección esperada para el escenario."""
    if scenario is Scenario.HIGHER_HUMIDITY:
        return _threshold(trait_value, worse_above=0.6, better_below=0.4)
    if scenario is Scenario.LOWER_HUMIDITY:
        return _threshold(1.0 - trait_value, worse_above=0.6, better_below=0.4)
    if scenario is Scenario.MORE_PRODUCT:
        return _threshold(1.0 - trait_value, worse_above=0.6, better_below=0.4)
    if scenario is Scenario.LESS_PRODUCT:
        return _threshold(trait_value, worse_above=0.6, better_below=0.4)
    if scenario is Scenario.ADD_PROTEIN:
        return _threshold(1.0 - trait_value, worse_above=0.6, better_below=0.4)
    if scenario is Scenario.REFRESH_INSTEAD_OF_WASH:
        return _threshold(1.0 - trait_value, worse_above=0.6, better_below=0.4)
    if scenario in {Scenario.SKIP_GEL, Scenario.STRETCH_WASH_DAY}:
        # Aquí el rasgo va en días, no normalizado: se compara con el umbral
        # práctico de "aguanta hasta el día siguiente".
        if trait_value >= 3.0:
            return Direction.LIKELY_SIMILAR, clamp((trait_value - 3.0) / 3.0)
        if trait_value <= 1.5:
            return Direction.LIKELY_WORSE, clamp((1.5 - trait_value) / 1.5)
        return Direction.LIKELY_SIMILAR, 0.3
    return Direction.UNKNOWN, 0.0


def _threshold(value: float, *, worse_above: float, better_below: float) -> tuple[Direction, float]:
    if value >= worse_above:
        return Direction.LIKELY_WORSE, clamp((value - worse_above) / (1.0 - worse_above))
    if value <= better_below:
        return Direction.LIKELY_BETTER, clamp((better_below - value) / better_below)
    return Direction.LIKELY_SIMILAR, 0.2
