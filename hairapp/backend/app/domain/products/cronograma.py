"""Cronograma capilar: agua, lípidos y proteína (marco dominante en LATAM).

Los envases en LATAM declaran su paso ("Paso del cronograma capilar:
Nutrición"), pero muchos no lo hacen, y algunos lo declaran de forma optimista.
Este módulo **deduce el paso del INCI**, para poder contrastar lo que dice la
etiqueta con lo que lleva la formulación.

El matiz de evidencia está en `app/data/rules/cronograma.yaml`: la distinción
entre las tres carencias es consenso profesional; el calendario fijo de días
asignados no lo es.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .catalog import Product
from .ingredients import Function, FunctionProfile, function_profile


class CronogramaStep(enum.Enum):
    HYDRATION = "hydration"
    """Carencia de agua. Se corrige con humectantes."""
    NUTRITION = "nutrition"
    """Carencia de lípidos. Se corrige con emolientes y aceites."""
    RECONSTRUCTION = "reconstruction"
    """Carencia de proteína. Se corrige con hidrolizados, con cautela."""

    @property
    def label_key(self) -> str:
        return f"cronograma.step.{self.value}"


@dataclass(frozen=True)
class StepInference:
    """Qué paso cubre una formulación, según lo que lleva dentro."""

    step: CronogramaStep | None
    scores: dict[CronogramaStep, float]
    confidence: float
    is_multi_step: bool
    """True cuando la formulación cubre varios pasos a la vez de forma
    apreciable. Es habitual y no es un defecto: solo hace que la etiqueta de
    "paso único" sea engañosa."""

    def as_dict(self) -> dict[str, object]:
        return {
            "step": self.step.value if self.step else None,
            "scores": {k.value: round(v, 3) for k, v in self.scores.items()},
            "confidence": round(self.confidence, 3),
            "is_multi_step": self.is_multi_step,
        }


#: Peso mínimo para considerar que un paso está cubierto de verdad y no por una
#: pizca puesta para poder nombrarlo en la etiqueta.
_PRESENCE_THRESHOLD = 0.02


def infer_step(profile: FunctionProfile) -> StepInference:
    """Deduce el paso del cronograma a partir del perfil funcional."""
    scores = {
        CronogramaStep.HYDRATION: profile.weight(Function.HUMECTANT),
        CronogramaStep.NUTRITION: (
            profile.weight(Function.EMOLLIENT)
            + profile.weight(Function.OCCLUSIVE)
            + profile.weight(Function.OIL_PENETRATING)
            + profile.weight(Function.OIL_SEALING)
        ),
        CronogramaStep.RECONSTRUCTION: profile.weight(Function.HYDROLYSED_PROTEIN),
    }

    present = {step: value for step, value in scores.items() if value >= _PRESENCE_THRESHOLD}
    if not present:
        return StepInference(None, scores, 0.0, False)

    total = sum(present.values())
    winner = max(present, key=lambda step: present[step])
    margin = present[winner] / total if total else 0.0

    return StepInference(
        step=winner,
        scores=scores,
        # La confianza baja cuando dos pasos están casi igualados: entonces la
        # formulación no "es" de un paso, hace dos cosas.
        confidence=min(margin, 0.8),
        is_multi_step=len(present) > 1 and margin < 0.6,
    )


def infer_for_product(product: Product) -> StepInference:
    return infer_step(function_profile(product.ingredients))


@dataclass(frozen=True)
class LabelCheck:
    """Contraste entre lo que declara la etiqueta y lo que lleva el INCI."""

    declared: CronogramaStep | None
    inferred: CronogramaStep | None
    agrees: bool
    message_key: str

    def as_dict(self) -> dict[str, object]:
        return {
            "declared": self.declared.value if self.declared else None,
            "inferred": self.inferred.value if self.inferred else None,
            "agrees": self.agrees,
            "message_key": self.message_key,
        }


def check_label(declared: CronogramaStep | None, inference: StepInference) -> LabelCheck:
    """Comprueba la etiqueta contra la formulación.

    No se acusa a nadie de mentir: una discrepancia se comunica como lo que es,
    "la etiqueta dice un paso y los ingredientes apuntan a otro", que es
    información útil para decidir. Muchos productos cubren dos pasos y eligen
    uno para la etiqueta.
    """
    if declared is None:
        return LabelCheck(None, inference.step, True, "cronograma.no_declared_step")
    if inference.step is None:
        return LabelCheck(declared, None, True, "cronograma.cannot_verify")
    if declared is inference.step:
        return LabelCheck(declared, inference.step, True, "cronograma.label_matches")
    if inference.is_multi_step:
        return LabelCheck(declared, inference.step, True, "cronograma.covers_several_steps")
    return LabelCheck(declared, inference.step, False, "cronograma.label_differs_from_inci")
