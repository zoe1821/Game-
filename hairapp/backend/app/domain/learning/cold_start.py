"""Arranque en frío: los primeros 0-5 wash days (requisito B2).

El problema: durante semanas el sistema no sabe nada de esta persona en
concreto. Las dos salidas fáciles son malas — inventar personalización que no
existe, o mostrar "confianza 0 %" hasta desmotivar.

Lo que hacemos: recomendar desde consenso cosmético general + el hair scan,
opcionalmente apoyado en **perfiles de referencia** anónimos con características
parecidas, **siempre etiquetado como tal**. Y convertir la falta de datos en el
plan explícito de la app: hitos que se ganan registrando, no gamificación
competitiva.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass

from ..common import Explanation, Measured, Source, clamp
from ..hair.attributes import Density, Porosity, StrandDiameter


class ColdStartStage(enum.Enum):
    NO_DATA = "no_data"
    """Perfil creado, ningún wash day registrado."""
    FIRST_STEPS = "first_steps"
    """1-2 registros."""
    EARLY_PATTERN = "early_pattern"
    """3-5 registros: empiezan a verse cosas, ninguna concluyente."""
    LEARNING = "learning"
    """6-11 registros."""
    ESTABLISHED = "established"
    """12 o más: el digital twin ya tiene con qué trabajar."""

    @property
    def label_key(self) -> str:
        return f"cold_start.stage.{self.value}"


def stage_for(entry_count: int) -> ColdStartStage:
    if entry_count <= 0:
        return ColdStartStage.NO_DATA
    if entry_count <= 2:
        return ColdStartStage.FIRST_STEPS
    if entry_count <= 5:
        return ColdStartStage.EARLY_PATTERN
    if entry_count <= 11:
        return ColdStartStage.LEARNING
    return ColdStartStage.ESTABLISHED


@dataclass(frozen=True)
class ReferenceProfile:
    """Perfil agregado y anónimo de personas con características parecidas.

    Se alimenta del banco de resultados agregados (B7), que solo recibe datos
    con consentimiento explícito y separado. Nunca contiene fotos ni nada
    identificable: solo características y qué funcionó, en agregado.
    """

    id: str
    porosity: Porosity
    density: Density
    strand_diameter: StrandDiameter
    pattern_family: str
    sample_size: int
    """Cuántas personas hay detrás de este agregado. Se muestra siempre."""
    top_techniques: tuple[str, ...] = ()
    top_product_attributes: tuple[tuple[str, str], ...] = ()
    avg_longevity_days: float | None = None

    def similarity(
        self,
        *,
        porosity: Porosity | None,
        density: Density | None,
        strand_diameter: StrandDiameter | None,
        pattern_family: str | None,
    ) -> float:
        """Parecido 0-1. Cada característica ausente resta, no se asume igual."""
        checks = (
            (porosity, self.porosity),
            (density, self.density),
            (strand_diameter, self.strand_diameter),
            (pattern_family, self.pattern_family),
        )
        score = 0.0
        for actual, reference in checks:
            if actual is None:
                continue
            score += 0.25 if actual == reference else 0.0
        return clamp(score)


#: Por debajo de este parecido no se usa el perfil de referencia: sugerir algo
#: "de gente como tú" cuando no se parece es peor que no sugerir nada.
MIN_SIMILARITY = 0.5

#: Un agregado de menos de esta cantidad de personas no es un agregado.
MIN_REFERENCE_SAMPLE = 20


@dataclass(frozen=True)
class ColdStartGuidance:
    stage: ColdStartStage
    entry_count: int
    reference_profile_id: str | None
    reference_sample_size: int
    suggested_technique_ids: tuple[str, ...]
    suggested_product_attributes: tuple[tuple[str, str], ...]
    milestone_keys: tuple[str, ...]
    message_key: str
    explanation: Explanation

    @property
    def is_based_on_reference_profiles(self) -> bool:
        return self.reference_profile_id is not None

    def as_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage.value,
            "entry_count": self.entry_count,
            "based_on_reference_profiles": self.is_based_on_reference_profiles,
            "reference_profile_id": self.reference_profile_id,
            "reference_sample_size": self.reference_sample_size,
            "suggested_technique_ids": list(self.suggested_technique_ids),
            "suggested_product_attributes": [list(p) for p in self.suggested_product_attributes],
            "milestone_keys": list(self.milestone_keys),
            "message_key": self.message_key,
            "explanation": self.explanation.as_dict(),
        }


#: Hitos por etapa. Son metas de utilidad, no puntos ni rachas: nada que
#: castigue saltarse un día ni que compare con otras personas (B7).
_MILESTONES: dict[ColdStartStage, tuple[str, ...]] = {
    ColdStartStage.NO_DATA: (
        "milestone.complete_first_scan",
        "milestone.log_first_wash_day",
        "milestone.add_what_you_already_own",
    ),
    ColdStartStage.FIRST_STEPS: (
        "milestone.log_day_2_result",
        "milestone.complete_zone_map",
    ),
    ColdStartStage.EARLY_PATTERN: (
        "milestone.log_three_more",
        "milestone.try_one_technique_change",
    ),
    ColdStartStage.LEARNING: (
        "milestone.run_first_experiment",
        "milestone.compare_photos",
    ),
    ColdStartStage.ESTABLISHED: ("milestone.review_your_twin",),
}


def guidance(
    *,
    entry_count: int,
    porosity: Measured[Porosity] | None = None,
    density: Measured[Density] | None = None,
    strand_diameter: Measured[StrandDiameter] | None = None,
    pattern_family: str | None = None,
    reference_profiles: Sequence[ReferenceProfile] = (),
    consented_to_reference_profiles: bool = True,
) -> ColdStartGuidance:
    """Qué puede ofrecer la app cuando todavía no conoce a esta persona.

    `consented_to_reference_profiles` respeta A22/B7: sin consentimiento no se
    usan datos agregados de nadie, y la app funciona igual, solo con consenso
    general.
    """
    stage = stage_for(entry_count)
    milestones = _MILESTONES[stage]

    best: ReferenceProfile | None = None
    best_similarity = 0.0
    if consented_to_reference_profiles:
        for profile in reference_profiles:
            if profile.sample_size < MIN_REFERENCE_SAMPLE:
                continue
            similarity = profile.similarity(
                porosity=porosity.value if porosity and porosity.confidence > 0 else None,
                density=density.value if density and density.confidence > 0 else None,
                strand_diameter=(
                    strand_diameter.value
                    if strand_diameter and strand_diameter.confidence > 0
                    else None
                ),
                pattern_family=pattern_family,
            )
            if similarity >= MIN_SIMILARITY and similarity > best_similarity:
                best, best_similarity = profile, similarity

    if best is not None:
        message_key = "cold_start.based_on_similar_profiles"
        uncertainty = (
            "uncertainty.not_your_history",
            "uncertainty.reference_profile_only",
            "uncertainty.cold_start",
        )
        explanation = Explanation(
            summary_key=message_key,
            inputs_used=("input.hair_scan", "input.reference_profiles"),
            observations=(
                f"similarity={best_similarity:.2f}",
                f"reference_sample_size={best.sample_size}",
            ),
            evidence_level="extended_anecdote",
            evidence_confidence=0.45,
            # Confianza personal cero: no es tu historial, y decirlo importa.
            personal_confidence=0.0,
            sample_size=entry_count,
            uncertainty_keys=uncertainty,
            alternatives=("cold_start.alternative.log_to_personalise",),
            params={
                "reference_profile_id": best.id,
                "source": Source.REFERENCE_PROFILE.value,
                "similarity": round(best_similarity, 2),
            },
        )
        return ColdStartGuidance(
            stage=stage,
            entry_count=entry_count,
            reference_profile_id=best.id,
            reference_sample_size=best.sample_size,
            suggested_technique_ids=best.top_techniques,
            suggested_product_attributes=best.top_product_attributes,
            milestone_keys=milestones,
            message_key=message_key,
            explanation=explanation,
        )

    message_key = "cold_start.general_consensus_only"
    explanation = Explanation(
        summary_key=message_key,
        inputs_used=("input.hair_scan", "input.cosmetic_consensus"),
        observations=(f"journal_entries={entry_count}",),
        evidence_level="professional_consensus",
        evidence_confidence=0.70,
        personal_confidence=0.0,
        sample_size=entry_count,
        uncertainty_keys=("uncertainty.cold_start", "uncertainty.no_personal_history"),
        alternatives=("cold_start.alternative.log_to_personalise",),
        params={"source": Source.INFERRED.value},
    )
    return ColdStartGuidance(
        stage=stage,
        entry_count=entry_count,
        reference_profile_id=None,
        reference_sample_size=0,
        suggested_technique_ids=(),
        suggested_product_attributes=(),
        milestone_keys=milestones,
        message_key=message_key,
        explanation=explanation,
    )
