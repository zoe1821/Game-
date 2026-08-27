"""Niveles de evidencia (requisito B4).

Toda regla y todo contenido educativo lleva exactamente una etiqueta. Una regla
sin etiqueta **no carga**: el loader lanza error en vez de asumir un valor por
defecto, porque un default silencioso convertiría "no lo sabemos" en "consenso".
"""

from __future__ import annotations

import enum


class EvidenceLevel(enum.Enum):
    SCIENTIFIC_EVIDENCE = "scientific_evidence"
    PROFESSIONAL_CONSENSUS = "professional_consensus"
    EXTENDED_ANECDOTE = "extended_anecdote"
    UNSUPPORTED_TREND = "unsupported_trend"

    @property
    def confidence(self) -> float:
        """`evidence_confidence`: qué tan sólida es la regla general.

        Deriva de la etiqueta, no se escribe a mano en cada regla. Así nadie
        puede subirle la confianza a una regla sin subirle también la etiqueta,
        que es una decisión visible y revisable.
        """
        return _EVIDENCE_CONFIDENCE[self]

    @property
    def label_key(self) -> str:
        return f"evidence.{self.value}"

    @property
    def can_recommend(self) -> bool:
        """Un mito nunca genera una recomendación; solo aparece desmontado."""
        return self is not EvidenceLevel.UNSUPPORTED_TREND


_EVIDENCE_CONFIDENCE: dict[EvidenceLevel, float] = {
    EvidenceLevel.SCIENTIFIC_EVIDENCE: 0.90,
    EvidenceLevel.PROFESSIONAL_CONSENSUS: 0.70,
    EvidenceLevel.EXTENDED_ANECDOTE: 0.45,
    EvidenceLevel.UNSUPPORTED_TREND: 0.00,
}
