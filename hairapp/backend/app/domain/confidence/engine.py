"""Sistema de confianza: `evidence_confidence` vs `personal_confidence`.

Este es el eje transversal del producto (docs/03-POSITIONING.md §3). Las dos
confianzas responden preguntas distintas:

  - evidence_confidence: ¿qué tan sólida es la regla general?
  - personal_confidence: ¿cuántos datos *tuyos* la respaldan?

**Nunca se promedian en un solo número.** Un promedio escondería exactamente la
distinción que el producto existe para hacer: "regla sólida pero solo 2 registros
tuyos" y "apenas anecdótico pero funciona en tus 14 registros" son situaciones
opuestas que un promedio volvería idénticas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from ..common import Explanation, clamp
from ..evidence.levels import EvidenceLevel


@dataclass(frozen=True)
class PersonalEvidence:
    """Lo que el historial de la persona dice sobre una regla concreta."""

    supporting: int = 0
    """Registros propios en los que la regla se cumplió."""
    contradicting: int = 0
    """Registros propios en los que no se cumplió."""
    most_recent: date | None = None
    controlled: bool = False
    """True si viene de un experimento controlado (A25), no de observación suelta."""

    @property
    def sample_size(self) -> int:
        return self.supporting + self.contradicting

    @property
    def agreement(self) -> float:
        """Proporción de acuerdo. 0.5 (indeciso) cuando no hay datos."""
        if self.sample_size == 0:
            return 0.5
        return self.supporting / self.sample_size


#: Nº de observaciones a partir del cual dejamos de penalizar por muestra corta.
#: No es un umbral mágico: es el punto donde la curva de saturación llega a ~0.8.
SAMPLE_SATURATION = 8

#: Días tras los cuales una observación pesa la mitad. El cabello cambia
#: (crece, se procesa, cambia la estación), así que un dato de hace un año no
#: vale lo mismo que uno de hace un mes.
RECENCY_HALF_LIFE_DAYS = 180


def personal_confidence(evidence: PersonalEvidence, *, today: date | None = None) -> float:
    """Confianza basada exclusivamente en el historial de la persona.

    Con muestra 0 devuelve 0.0, no 0.5: no tener datos no es "medio seguro",
    es no saber. La app lo comunica como cold start (B2), no como confianza baja.

    **Es una medida de fuerza, no de dirección.** Un historial de 1 a favor y 13
    en contra produce confianza personal *alta*: sabemos bastante bien qué pasa
    contigo, y lo que sabemos es que la regla no se te aplica. La dirección la
    da `ConfidenceReport.contradicts_personal_history` / `personal_direction`;
    quien consuma esto debe mirar las dos cosas.
    """
    if evidence.sample_size == 0:
        return 0.0

    # Saturación por tamaño de muestra: crece rápido al principio y se aplana.
    size_factor = 1.0 - math.exp(-evidence.sample_size / (SAMPLE_SATURATION / 2))

    # Acuerdo, reescalado para que 50/50 valga 0 y no 0.5.
    agreement_factor = abs(evidence.agreement - 0.5) * 2.0

    # Un experimento controlado vale más que la misma cantidad de observación suelta.
    control_bonus = 1.15 if evidence.controlled else 1.0

    recency_factor = _recency_factor(evidence.most_recent, today)

    raw = size_factor * agreement_factor * control_bonus * recency_factor
    return clamp(raw)


def _recency_factor(most_recent: date | None, today: date | None) -> float:
    if most_recent is None:
        return 0.7
    reference = today or date.today()
    age_days = max(0, (reference - most_recent).days)
    return clamp(0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS), low=0.2, high=1.0)


@dataclass(frozen=True)
class ConfidenceReport:
    """Las dos confianzas, por separado, con su contexto."""

    evidence_level: EvidenceLevel
    evidence_confidence: float
    personal_confidence: float
    sample_size: int
    is_cold_start: bool
    uncertainty_keys: tuple[str, ...]
    contradicts_personal_history: bool = False
    agreement: float = 0.5

    @property
    def personal_direction(self) -> str:
        """Hacia dónde apunta el historial propio: `supports`, `contradicts`
        o `unknown`. Complementa a `personal_confidence`, que solo mide fuerza."""
        if self.sample_size == 0:
            return "unknown"
        if self.contradicts_personal_history:
            return "contradicts"
        if self.personal_confidence < 0.15:
            return "unknown"
        return "supports"

    def as_explanation(
        self,
        *,
        summary_key: str,
        inputs_used: tuple[str, ...] = (),
        observations: tuple[str, ...] = (),
        alternatives: tuple[str, ...] = (),
        params: dict[str, object] | None = None,
    ) -> Explanation:
        return Explanation(
            summary_key=summary_key,
            inputs_used=inputs_used,
            observations=observations,
            evidence_level=self.evidence_level.value,
            evidence_confidence=self.evidence_confidence,
            personal_confidence=self.personal_confidence,
            sample_size=self.sample_size,
            uncertainty_keys=self.uncertainty_keys,
            alternatives=alternatives,
            params=params or {},
        )


#: Por debajo de esta muestra consideramos que seguimos en arranque en frío (B2).
COLD_START_SAMPLE_THRESHOLD = 3


def build_report(
    level: EvidenceLevel,
    evidence: PersonalEvidence,
    *,
    extra_uncertainty: tuple[str, ...] = (),
    today: date | None = None,
) -> ConfidenceReport:
    personal = personal_confidence(evidence, today=today)
    cold = evidence.sample_size < COLD_START_SAMPLE_THRESHOLD

    uncertainty: list[str] = list(extra_uncertainty)
    if cold:
        uncertainty.append("uncertainty.cold_start")
    if 0 < evidence.sample_size < SAMPLE_SATURATION:
        uncertainty.append("uncertainty.small_sample")
    if evidence.sample_size and 0.35 <= evidence.agreement <= 0.65:
        uncertainty.append("uncertainty.mixed_personal_results")
    if level is EvidenceLevel.EXTENDED_ANECDOTE:
        uncertainty.append("uncertainty.anecdotal_rule")
    if not evidence.controlled and evidence.sample_size >= SAMPLE_SATURATION:
        uncertainty.append("uncertainty.uncontrolled_observations")

    contradicts = evidence.sample_size >= COLD_START_SAMPLE_THRESHOLD and evidence.agreement < 0.35
    if contradicts:
        uncertainty.append("uncertainty.contradicts_your_history")

    return ConfidenceReport(
        evidence_level=level,
        evidence_confidence=level.confidence,
        personal_confidence=personal,
        sample_size=evidence.sample_size,
        is_cold_start=cold,
        uncertainty_keys=tuple(dict.fromkeys(uncertainty)),
        contradicts_personal_history=contradicts,
        agreement=evidence.agreement,
    )


def photo_quality_penalty(quality_score: float) -> float:
    """Cuánto baja la confianza de una estimación por la calidad de la foto.

    Devuelve un multiplicador. Una foto mediocre no invalida la estimación,
    pero tampoco puede producir la misma confianza que una buena.
    """
    return clamp(0.35 + 0.65 * clamp(quality_score), low=0.2, high=1.0)


def conflict_penalty(n_conflicting_signals: int) -> float:
    """Penalización cuando señales independientes se contradicen.

    Ejemplo real: el historial químico dice "decolorado" (sugiere porosidad
    alta) pero el comportamiento con agua declarado sugiere porosidad baja. La
    respuesta correcta no es elegir una y presentarla con confianza alta.
    """
    if n_conflicting_signals <= 0:
        return 1.0
    return clamp(0.85 ** n_conflicting_signals, low=0.3, high=1.0)
