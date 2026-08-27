"""Primitivas compartidas por todo el dominio.

Este módulo es Python puro: no importa FastAPI, SQLAlchemy ni nada de red.
Esa restricción es deliberada (ver docs/01-ARCHITECTURE.md §1) y está
verificada por `tests/test_domain_purity.py`.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Generic, TypeVar

T = TypeVar("T")


class Source(enum.Enum):
    """De dónde viene un valor estimado.

    El orden importa: `USER` gana siempre sobre cualquier otra fuente (A1.4).
    """

    USER = "user"
    AI_VISION = "ai_vision"
    INFERRED = "inferred"
    REFERENCE_PROFILE = "reference_profile"
    DEFAULT = "default"

    @property
    def priority(self) -> int:
        return _SOURCE_PRIORITY[self]

    @property
    def confidence_ceiling(self) -> float:
        """Techo de confianza que esta fuente puede alcanzar.

        Ninguna estimación automática llega a 1.0: solo una confirmación
        explícita de la persona usuaria lo hace.
        """
        return _SOURCE_CEILING[self]


_SOURCE_PRIORITY: dict[Source, int] = {
    Source.USER: 100,
    Source.AI_VISION: 60,
    Source.INFERRED: 50,
    Source.REFERENCE_PROFILE: 30,
    Source.DEFAULT: 10,
}

_SOURCE_CEILING: dict[Source, float] = {
    Source.USER: 1.0,
    Source.AI_VISION: 0.85,
    Source.INFERRED: 0.80,
    Source.REFERENCE_PROFILE: 0.45,
    Source.DEFAULT: 0.25,
}


class MeasurementError(ValueError):
    """Se intentó construir una medición inválida."""


@dataclass(frozen=True)
class Measured(Generic[T]):
    """Un valor con procedencia y confianza.

    Nada estimado entra al perfil sin este envoltorio. Es lo que hace posible
    la explicabilidad (A21) sin trabajo adicional en cada pantalla.
    """

    value: T
    source: Source
    confidence: float
    observed_at: date | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise MeasurementError(
                f"confidence debe estar entre 0 y 1, recibido {self.confidence!r}"
            )
        ceiling = self.source.confidence_ceiling
        if self.confidence > ceiling:
            raise MeasurementError(
                f"la fuente {self.source.value} no puede superar una confianza de "
                f"{ceiling}; recibido {self.confidence}"
            )

    @property
    def is_user_confirmed(self) -> bool:
        return self.source is Source.USER

    def with_confidence(self, confidence: float) -> Measured[T]:
        capped = min(confidence, self.source.confidence_ceiling)
        return replace(self, confidence=max(0.0, capped))


def user_value(value: T, *, observed_at: date | None = None, notes: str | None = None) -> Measured[T]:
    """Atajo para un valor confirmado o corregido por la persona usuaria."""
    return Measured(value=value, source=Source.USER, confidence=1.0, observed_at=observed_at, notes=notes)


def resolve(candidates: Iterable[Measured[T]]) -> Measured[T] | None:
    """Elige el valor vigente entre varias estimaciones de la misma propiedad.

    Criterio: primero prioridad de fuente (USER gana siempre), después
    confianza, después recencia. Nunca promedia fuentes distintas: promediar
    una corrección manual con una estimación automática destruiría la
    corrección, que es justo lo que A1.4 prohíbe.
    """
    best: Measured[T] | None = None
    for candidate in candidates:
        if best is None:
            best = candidate
            continue
        if _rank(candidate) > _rank(best):
            best = candidate
    return best


def _rank(m: Measured[T]) -> tuple[int, float, date]:
    return (m.source.priority, m.confidence, m.observed_at or date.min)


@dataclass(frozen=True)
class Unavailable:
    """Resultado honesto cuando una etapa no puede producir un valor.

    Se usa en vez de inventar un número (regla crítica del proyecto). El
    `reason_key` se traduce en el cliente; el backend no manda texto de UI.
    """

    reason_key: str
    detail: str | None = None


@dataclass(frozen=True)
class Explanation:
    """Bloque "¿por qué esto?" (A21). Acompaña a toda recomendación relevante.

    `evidence_confidence` y `personal_confidence` se muestran por separado y
    nunca se promedian: son cosas distintas (ver docs/08-EVIDENCE-POLICY.md).
    """

    summary_key: str
    inputs_used: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    evidence_level: str = "professional_consensus"
    evidence_confidence: float = 0.0
    personal_confidence: float = 0.0
    sample_size: int = 0
    uncertainty_keys: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    params: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "summary_key": self.summary_key,
            "inputs_used": list(self.inputs_used),
            "observations": list(self.observations),
            "evidence_level": self.evidence_level,
            "evidence_confidence": round(self.evidence_confidence, 3),
            "personal_confidence": round(self.personal_confidence, 3),
            "sample_size": self.sample_size,
            "uncertainty_keys": list(self.uncertainty_keys),
            "alternatives": list(self.alternatives),
            "params": dict(self.params),
        }


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
