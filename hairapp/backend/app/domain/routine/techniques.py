"""Biblioteca de técnicas (A9).

Cada técnica declara: para quién suele funcionar, qué resultado busca, su
dificultad, cuánto tarda, y — crucialmente — su nivel de evidencia. Muchas
técnicas populares son experiencia extendida, no consenso; decirlo es parte del
producto.

Los pasos son claves i18n, no texto: el backend no manda copy de UI.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from ..evidence.levels import EvidenceLevel
from ..hair.attributes import PatternFamily, Porosity


class TechniqueStage(enum.Enum):
    CLEANSE = "cleanse"
    CONDITION = "condition"
    DETANGLE = "detangle"
    APPLY_STYLER = "apply_styler"
    DRY = "dry"
    REFRESH = "refresh"
    NIGHT = "night"


class Difficulty(enum.Enum):
    EASY = "easy"
    MODERATE = "moderate"
    ADVANCED = "advanced"


@dataclass(frozen=True)
class Technique:
    id: str
    stage: TechniqueStage
    evidence_level: EvidenceLevel
    difficulty: Difficulty
    minutes: int
    goal_keys: tuple[str, ...]
    suits_patterns: tuple[PatternFamily, ...]
    suits_porosity: tuple[Porosity, ...] = ()
    step_keys: tuple[str, ...] = ()
    timer_steps: tuple[int, ...] = ()
    """Duración en segundos de cada paso que lleva temporizador (0 = sin)."""
    caution_keys: tuple[str, ...] = ()
    not_for_keys: tuple[str, ...] = ()

    @property
    def name_key(self) -> str:
        return f"technique.{self.id}.name"

    @property
    def description_key(self) -> str:
        return f"technique.{self.id}.description"

    def suits(self, family: PatternFamily, porosity: Porosity | None = None) -> bool:
        if family not in self.suits_patterns:
            return False
        if self.suits_porosity and porosity is not None and porosity not in self.suits_porosity:
            return False
        return True


TECHNIQUES: tuple[Technique, ...] = (
    Technique(
        id="praying_hands",
        stage=TechniqueStage.APPLY_STYLER,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=3,
        goal_keys=("goal.definition", "goal.frizz_control"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY),
        step_keys=(
            "technique.praying_hands.step.1",
            "technique.praying_hands.step.2",
            "technique.praying_hands.step.3",
        ),
        timer_steps=(0, 0, 0),
        caution_keys=("technique.praying_hands.caution.length",),
    ),
    Technique(
        id="raking",
        stage=TechniqueStage.APPLY_STYLER,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=3,
        goal_keys=("goal.even_distribution", "goal.volume"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=("technique.raking.step.1", "technique.raking.step.2"),
        caution_keys=("technique.raking.caution.separates_clumps",),
    ),
    Technique(
        id="shingling",
        stage=TechniqueStage.APPLY_STYLER,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.ADVANCED,
        minutes=35,
        goal_keys=("goal.definition", "goal.clumping"),
        suits_patterns=(PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=(
            "technique.shingling.step.1",
            "technique.shingling.step.2",
            "technique.shingling.step.3",
            "technique.shingling.step.4",
        ),
        caution_keys=("technique.shingling.caution.time",),
    ),
    Technique(
        id="plopping",
        stage=TechniqueStage.DRY,
        evidence_level=EvidenceLevel.EXTENDED_ANECDOTE,
        difficulty=Difficulty.EASY,
        minutes=15,
        goal_keys=("goal.volume", "goal.definition"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY),
        step_keys=("technique.plopping.step.1", "technique.plopping.step.2", "technique.plopping.step.3"),
        timer_steps=(0, 0, 900),
        not_for_keys=("technique.plopping.not_for.very_long_dense",),
    ),
    Technique(
        id="diffusing",
        stage=TechniqueStage.DRY,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.MODERATE,
        minutes=20,
        goal_keys=("goal.definition", "goal.volume", "goal.frizz_control"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=(
            "technique.diffusing.step.1",
            "technique.diffusing.step.2",
            "technique.diffusing.step.3",
            "technique.diffusing.step.4",
        ),
        timer_steps=(0, 300, 300, 0),
        caution_keys=("technique.diffusing.caution.heat",),
    ),
    Technique(
        id="squish_to_condish",
        stage=TechniqueStage.CONDITION,
        evidence_level=EvidenceLevel.EXTENDED_ANECDOTE,
        difficulty=Difficulty.EASY,
        minutes=5,
        goal_keys=("goal.hydration", "goal.clumping"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY),
        suits_porosity=(Porosity.MEDIUM, Porosity.HIGH, Porosity.MIXED),
        step_keys=("technique.squish_to_condish.step.1", "technique.squish_to_condish.step.2"),
    ),
    Technique(
        id="scrunch_out_the_crunch",
        stage=TechniqueStage.DRY,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=2,
        goal_keys=("goal.definition", "goal.softness"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=("technique.scrunch_out_the_crunch.step.1", "technique.scrunch_out_the_crunch.step.2"),
        caution_keys=("technique.scrunch_out_the_crunch.caution.fully_dry",),
    ),
    Technique(
        id="finger_coiling",
        stage=TechniqueStage.APPLY_STYLER,
        evidence_level=EvidenceLevel.EXTENDED_ANECDOTE,
        difficulty=Difficulty.ADVANCED,
        minutes=45,
        goal_keys=("goal.definition",),
        suits_patterns=(PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=("technique.finger_coiling.step.1", "technique.finger_coiling.step.2"),
        caution_keys=("technique.finger_coiling.caution.time",),
    ),
    Technique(
        id="detangle_from_ends",
        stage=TechniqueStage.DETANGLE,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=10,
        goal_keys=("goal.damage_recovery", "goal.length_retention"),
        suits_patterns=(PatternFamily.STRAIGHT, PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=(
            "technique.detangle_from_ends.step.1",
            "technique.detangle_from_ends.step.2",
            "technique.detangle_from_ends.step.3",
        ),
    ),
    Technique(
        id="pineapple",
        stage=TechniqueStage.NIGHT,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=2,
        goal_keys=("goal.preserve_style", "goal.volume"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY),
        step_keys=("technique.pineapple.step.1", "technique.pineapple.step.2"),
        not_for_keys=("technique.pineapple.not_for.short_hair",),
    ),
    Technique(
        id="bonnet_or_satin",
        stage=TechniqueStage.NIGHT,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=1,
        goal_keys=("goal.preserve_style", "goal.frizz_control", "goal.length_retention"),
        suits_patterns=(PatternFamily.STRAIGHT, PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=("technique.bonnet_or_satin.step.1",),
    ),
    Technique(
        id="refresh_spray_and_scrunch",
        stage=TechniqueStage.REFRESH,
        evidence_level=EvidenceLevel.PROFESSIONAL_CONSENSUS,
        difficulty=Difficulty.EASY,
        minutes=5,
        goal_keys=("goal.refresh", "goal.definition"),
        suits_patterns=(PatternFamily.WAVY, PatternFamily.CURLY, PatternFamily.COILY),
        step_keys=("technique.refresh_spray_and_scrunch.step.1", "technique.refresh_spray_and_scrunch.step.2"),
    ),
)

TECHNIQUES_BY_ID: dict[str, Technique] = {t.id: t for t in TECHNIQUES}


def techniques_for(
    stage: TechniqueStage,
    family: PatternFamily,
    *,
    porosity: Porosity | None = None,
    max_minutes: int | None = None,
) -> list[Technique]:
    """Técnicas aplicables, ordenadas por evidencia y luego por rapidez."""
    found = [
        t
        for t in TECHNIQUES
        if t.stage is stage
        and t.suits(family, porosity)
        and (max_minutes is None or t.minutes <= max_minutes)
    ]
    found.sort(key=lambda t: (-t.evidence_level.confidence, t.minutes))
    return found
