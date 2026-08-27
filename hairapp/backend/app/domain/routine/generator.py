"""Generador de rutinas por zona (A8).

Requisito duro del brief: instrucciones **extremadamente específicas** por zona
— producto, cantidad, técnica, orden, tensión, secado, temperatura. Nunca
"aplica producto y define". Cada paso generado lleva su explicación (A21) con
las dos confianzas separadas y el tamaño de muestra.

El generador no elige productos comerciales: elige **atributos** de producto
(fuerza de tensioactivo, nivel de proteína, tipo de fijación). El emparejamiento
con productos concretos ocurre después, y empieza por el inventario (A15).
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ..common import Explanation
from ..hair.attributes import (
    CurlPattern,
    Density,
    PatternFamily,
    Porosity,
    ProcessingState,
    StrandDiameter,
)
from ..hair.zones import Zone
from ..rules.engine import (
    EvaluatedRule,
    EvaluationResult,
    PersonalEvidenceLookup,
    RuleEngine,
    no_personal_history,
)
from ..rules.model import RuleKind
from .amounts import Amount, ProductCategory, closest_reference, compute_amount
from .techniques import TECHNIQUES_BY_ID, Technique, TechniqueStage, techniques_for


class Goal(enum.Enum):
    DEFINITION = "definition"
    VOLUME = "volume"
    FRIZZ_CONTROL = "frizz_control"
    HYDRATION = "hydration"
    DAMAGE_RECOVERY = "damage_recovery"
    LENGTH_RETENTION = "length_retention"
    SCALP_COMFORT = "scalp_comfort"
    CHEMICAL_TRANSITION = "chemical_transition"
    PRESERVE_STYLE = "preserve_style"
    LOW_MAINTENANCE = "low_maintenance"
    SHINE = "shine"
    CLUMPING = "clumping"


class RoutineKind(enum.Enum):
    WASH_DAY = "wash_day"
    REFRESH = "refresh"
    NIGHT = "night"
    QUICK_5 = "quick_5"
    QUICK_10 = "quick_10"
    QUICK_20 = "quick_20"


@dataclass
class ZoneState:
    """El estado de una zona tal como lo usa el generador.

    Valores ya resueltos (`Measured.value`); la confianza viaja aparte, en
    `confidence_by_field`, para que el paso generado pueda declarar qué tan
    seguro está de cada entrada que usó.
    """

    zone: Zone
    pattern: CurlPattern | None = None
    porosity: Porosity | None = None
    density: Density | None = None
    strand_diameter: StrandDiameter | None = None
    processing: ProcessingState | None = None
    length_cm: float | None = None
    frizz_level: float | None = None
    damage_signs: tuple[str, ...] = ()
    confidence_by_field: Mapping[str, float] = field(default_factory=dict)

    @property
    def pattern_family(self) -> PatternFamily | None:
        return self.pattern.family if self.pattern else None


@dataclass
class RoutineContext:
    """Todo lo que el generador necesita saber, ya reunido."""

    zones: Sequence[ZoneState]
    goals: Sequence[Goal]
    kind: RoutineKind = RoutineKind.WASH_DAY
    weather: Mapping[str, Any] = field(default_factory=dict)
    water_hardness_ppm: float | None = None
    scalp_observations: tuple[str, ...] = ()
    scalp_referral_signs: tuple[str, ...] = ()
    uses_heat: bool = False
    owns_diffuser: bool = False
    uses_cowash: bool = False
    protein_frequency_per_month: int = 0
    reports_stiff_hair: bool = False
    protective_style: str = "none"
    available_minutes: int | None = None

    @property
    def primary_goal(self) -> Goal | None:
        return self.goals[0] if self.goals else None


@dataclass(frozen=True)
class RoutineStep:
    """Un paso concreto. Todo lo que hace falta para ejecutarlo, sin ambigüedad."""

    order: int
    stage: TechniqueStage
    action_key: str
    zones: tuple[Zone, ...]
    product_category: ProductCategory | None
    product_attributes: Mapping[str, Any]
    amount: Amount | None
    technique: Technique | None
    params: Mapping[str, Any]
    explanation: Explanation
    duration_seconds: int | None = None
    follow_up_techniques: tuple[Technique, ...] = ()
    """Técnicas que van después de la principal en el mismo paso: difundir y
    luego romper el cast son dos gestos de un mismo momento, no dos pasos."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "stage": self.stage.value,
            "action_key": self.action_key,
            "zones": [z.value for z in self.zones],
            "product_category": self.product_category.value if self.product_category else None,
            "product_attributes": dict(self.product_attributes),
            "amount": self.amount.as_dict() if self.amount else None,
            "technique_id": self.technique.id if self.technique else None,
            "technique_steps": list(self.technique.step_keys) if self.technique else [],
            "follow_up_technique_ids": [t.id for t in self.follow_up_techniques],
            "params": dict(self.params),
            "duration_seconds": self.duration_seconds,
            "explanation": self.explanation.as_dict(),
        }


@dataclass(frozen=True)
class GeneratedRoutine:
    kind: RoutineKind
    steps: tuple[RoutineStep, ...]
    warnings: tuple[Explanation, ...]
    education: tuple[Explanation, ...] = ()
    halted: bool = False
    halt_block_key: str | None = None
    skipped_reason_keys: tuple[str, ...] = ()

    @property
    def total_minutes(self) -> int:
        seconds = sum(s.duration_seconds or 0 for s in self.steps)
        technique_minutes = sum(s.technique.minutes for s in self.steps if s.technique)
        return max(technique_minutes, seconds // 60)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "halted": self.halted,
            "halt_block_key": self.halt_block_key,
            "total_minutes": self.total_minutes,
            "steps": [s.as_dict() for s in self.steps],
            "warnings": [w.as_dict() for w in self.warnings],
            "education": [e.as_dict() for e in self.education],
            "skipped_reason_keys": list(self.skipped_reason_keys),
        }


#: Orden canónico de un wash day. El orden importa de verdad: aplicar gel antes
#: que la crema cambia el resultado, y aplicar sobre cabello ya escurrido cambia
#: la distribución.
#:
#: Cada entrada declara qué `step` de regla la alimenta. Ese emparejamiento es
#: exacto a propósito: sin él, una regla que pide fijación fuerte para el gel
#: acabaría poniendo fijación fuerte también en el acondicionador sin dejar,
#: que es un resultado sin sentido.


@dataclass(frozen=True)
class StepSpec:
    stage: TechniqueStage
    action_key: str
    category: ProductCategory | None
    rule_steps: frozenset[str] = frozenset()
    optional: bool = False
    """Si es opcional, el paso solo aparece cuando alguna regla lo pide."""
    accepts_global_attributes: bool = False
    """Si acepta atributos de reglas sin `step` (clima, agua): los emolientes y
    filtros UV sí van en los productos que se quedan en el cabello."""
    default_duration_seconds: int | None = None


_WASH_DAY_STEPS: tuple[StepSpec, ...] = (
    StepSpec(TechniqueStage.CLEANSE, "step.chelate", ProductCategory.CLARIFYING_SHAMPOO,
             frozenset({"chelate"}), optional=True),
    StepSpec(TechniqueStage.CLEANSE, "step.clarify", ProductCategory.CLARIFYING_SHAMPOO,
             frozenset({"clarify"}), optional=True),
    StepSpec(TechniqueStage.CLEANSE, "step.cleanse", ProductCategory.SHAMPOO,
             frozenset({"cleanse"})),
    StepSpec(TechniqueStage.CONDITION, "step.protein", ProductCategory.PROTEIN_TREATMENT,
             frozenset({"protein_treatment"}), optional=True, default_duration_seconds=300),
    StepSpec(TechniqueStage.CONDITION, "step.deep_condition", ProductCategory.DEEP_CONDITIONER,
             frozenset({"deep_condition"}), optional=True, default_duration_seconds=1200),
    StepSpec(TechniqueStage.CONDITION, "step.condition", ProductCategory.CONDITIONER,
             frozenset({"condition"})),
    StepSpec(TechniqueStage.DETANGLE, "step.detangle", None),
    StepSpec(TechniqueStage.APPLY_STYLER, "step.leave_in", ProductCategory.LEAVE_IN,
             frozenset({"leave_in"}), accepts_global_attributes=True),
    StepSpec(TechniqueStage.APPLY_STYLER, "step.cream", ProductCategory.CREAM,
             frozenset({"cream"}), optional=True, accepts_global_attributes=True),
    StepSpec(TechniqueStage.APPLY_STYLER, "step.gel", ProductCategory.GEL,
             frozenset({"style", "gel"}), accepts_global_attributes=True),
    StepSpec(TechniqueStage.DRY, "step.dry", None, frozenset({"heat_styling"})),
)

_REFRESH_STEPS: tuple[StepSpec, ...] = (
    StepSpec(TechniqueStage.REFRESH, "step.refresh", ProductCategory.LEAVE_IN,
             accepts_global_attributes=True),
)

_NIGHT_STEPS: tuple[StepSpec, ...] = (
    StepSpec(TechniqueStage.NIGHT, "step.night", None),
)

#: Categorías que van solo al cuero cabelludo: no se aplican en las puntas.
_SCALP_ONLY_CATEGORIES = {
    ProductCategory.SHAMPOO,
    ProductCategory.CLARIFYING_SHAMPOO,
    ProductCategory.SCALP_PRODUCT,
}

#: Orden natural de las técnicas dentro de una misma etapa: primero se seca,
#: después se rompe la película.
_STAGE_TECHNIQUE_ORDER: dict[str, int] = {
    "plopping": 10,
    "diffusing": 20,
    "scrunch_out_the_crunch": 30,
}

_QUICK_LIMITS = {RoutineKind.QUICK_5: 5, RoutineKind.QUICK_10: 10, RoutineKind.QUICK_20: 20}


class RoutineGenerator:
    def __init__(self, engine: RuleEngine) -> None:
        self._engine = engine

    def generate(
        self,
        context: RoutineContext,
        *,
        personal: PersonalEvidenceLookup = no_personal_history,
        today: date | None = None,
    ) -> GeneratedRoutine:
        # 1. Señales de derivación: se comprueban antes que nada y detienen todo.
        if context.scalp_referral_signs:
            result = self._engine.evaluate(
                {"scalp.referral_signs": list(context.scalp_referral_signs)},
                personal=personal,
                today=today,
            )
            if result.halted:
                return GeneratedRoutine(
                    kind=context.kind,
                    steps=(),
                    warnings=(),
                    halted=True,
                    halt_block_key=result.halt_block_key,
                )

        # 2. Reglas globales (clima, agua, calor, cuero cabelludo, estilo).
        global_result = self._engine.evaluate(
            self._global_facts(context), personal=personal, today=today
        )

        # 3. Reglas por zona. Cada zona se evalúa por separado: eso es lo que
        #    permite que la coronilla reciba una instrucción distinta de la nuca.
        zone_results: dict[Zone, EvaluationResult] = {}
        for zone_state in context.zones:
            facts = self._zone_facts(zone_state, context)
            zone_results[zone_state.zone] = self._engine.evaluate(
                facts, personal=personal, today=today
            )

        steps = self._build_steps(context, global_result, zone_results)
        warnings = self._collect(global_result, zone_results, RuleKind.WARNING)
        education = self._collect(global_result, zone_results, RuleKind.EDUCATION)
        steps, skipped = self._apply_time_budget(steps, context)

        return GeneratedRoutine(
            kind=context.kind,
            steps=tuple(steps),
            warnings=tuple(warnings),
            education=tuple(education),
            skipped_reason_keys=tuple(skipped),
        )

    # -- hechos -----------------------------------------------------------

    def _global_facts(self, context: RoutineContext) -> dict[str, Any]:
        facts: dict[str, Any] = {
            "routine.uses_heat": context.uses_heat,
            "routine.uses_cowash": context.uses_cowash,
            "routine.protein_frequency_per_month": context.protein_frequency_per_month,
            "routine.protective_style": context.protective_style,
            "user.owns_diffuser": context.owns_diffuser,
            "user.reports_stiff_hair": context.reports_stiff_hair,
            "scalp.observations": list(context.scalp_observations),
            "scalp.buildup": "buildup" in context.scalp_observations,
        }
        if context.primary_goal:
            facts["goal.primary"] = context.primary_goal.value
        if context.water_hardness_ppm is not None:
            facts["water.hardness_ppm"] = context.water_hardness_ppm
        for key, value in context.weather.items():
            facts[f"weather.{key}"] = value
        return facts

    def _zone_facts(self, zone_state: ZoneState, context: RoutineContext) -> dict[str, Any]:
        facts = self._global_facts(context)
        facts["zone.id"] = zone_state.zone.value
        if zone_state.porosity:
            facts["zone.porosity"] = zone_state.porosity.value
        if zone_state.density:
            facts["zone.density"] = zone_state.density.value
        if zone_state.strand_diameter:
            facts["zone.strand_diameter"] = zone_state.strand_diameter.value
        if zone_state.processing:
            facts["zone.processing"] = zone_state.processing.value
        if zone_state.pattern:
            facts["zone.pattern"] = zone_state.pattern.value
            facts["zone.pattern_family"] = zone_state.pattern.family.value
        if zone_state.frizz_level is not None:
            facts["zone.frizz_level"] = zone_state.frizz_level
        facts["zone.damage_signs"] = list(zone_state.damage_signs)
        return facts

    # -- construcción de pasos --------------------------------------------

    def _build_steps(
        self,
        context: RoutineContext,
        global_result: EvaluationResult,
        zone_results: Mapping[Zone, EvaluationResult],
    ) -> list[RoutineStep]:
        steps: list[RoutineStep] = []
        order = 1

        for spec in self._specs_for(context.kind):
            grouped = self._group_zones_by_instruction(context, zone_results, spec)
            for instruction in grouped:
                steps.append(self._make_step(order, instruction, context, global_result))
                order += 1

        return steps

    def _specs_for(self, kind: RoutineKind) -> tuple[StepSpec, ...]:
        if kind is RoutineKind.REFRESH:
            return _REFRESH_STEPS
        if kind is RoutineKind.NIGHT:
            return _NIGHT_STEPS
        # Los modos rápidos usan el mismo orden; la poda por tiempo va después.
        return _WASH_DAY_STEPS

    def _group_zones_by_instruction(
        self,
        context: RoutineContext,
        zone_results: Mapping[Zone, EvaluationResult],
        spec: StepSpec,
    ) -> list[_Instruction]:
        """Agrupa zonas que reciben exactamente la misma instrucción.

        Esto es lo que evita una lista de quince pasos idénticos: si toda la
        cabeza lleva el mismo gel, es un paso; si la coronilla necesita otra
        cosa, se separa sola.
        """
        buckets: dict[tuple[Any, ...], _Instruction] = {}

        for zone_state in context.zones:
            if spec.category in _SCALP_ONLY_CATEGORIES and zone_state.zone is Zone.ENDS:
                continue
            result = zone_results[zone_state.zone]
            attributes, modifier, contributing = self._attributes_for(result, spec)

            if spec.optional and not any(
                e.rule.outcome.get("step") in spec.rule_steps for e in contributing.values()
            ):
                # Un paso opcional solo existe si alguna regla lo pidió. No se
                # añade una mascarilla «por si acaso».
                continue

            technique, follow_ups = self._technique_for(spec.stage, zone_state, context, result)
            key = (
                tuple(sorted((k, _hashable(v)) for k, v in attributes.items())),
                round(modifier, 2),
                technique.id if technique else None,
                tuple(t.id for t in follow_ups),
            )
            if key in buckets:
                buckets[key].zones.append(zone_state)
                buckets[key].rules.update(contributing)
            else:
                buckets[key] = _Instruction(
                    spec=spec,
                    attributes=attributes,
                    modifier=modifier,
                    technique=technique,
                    follow_ups=follow_ups,
                    zones=[zone_state],
                    rules=dict(contributing),
                )

        return list(buckets.values())

    def _attributes_for(
        self, result: EvaluationResult, spec: StepSpec
    ) -> tuple[dict[str, Any], float, dict[str, EvaluatedRule]]:
        """Reúne los atributos de producto que aplican a este paso concreto.

        Se aplican en orden ascendente de prioridad efectiva, de modo que la
        regla más fuerte escribe la última y gana el conflicto. Al revés, una
        regla débil sobrescribiría a una sólida en silencio.
        """
        attributes: dict[str, Any] = {}
        modifier = 1.0
        # Indexadas por id: `Rule` lleva mapas en `outcome`, así que no es
        # hashable y no puede vivir en un set.
        contributing: dict[str, EvaluatedRule] = {}

        ascending = sorted(result.active, key=lambda e: e.effective_priority)

        for evaluated in ascending:
            rule = evaluated.rule
            if not rule.can_recommend:
                continue
            outcome = rule.outcome
            step_name = outcome.get("step")

            if step_name is not None:
                if str(step_name) not in spec.rule_steps:
                    continue
                if "product_attributes" in outcome:
                    attributes.update(dict(outcome["product_attributes"]))
                if "amount_modifier" in outcome:
                    modifier *= float(outcome["amount_modifier"])
                if "frequency_hint" in outcome:
                    attributes.setdefault("frequency_hint", outcome["frequency_hint"])
                contributing[rule.id] = evaluated
                continue

            # Reglas sin `step`: clima, agua, técnica. Solo tocan los productos
            # que se quedan en el cabello, no el champú, que se enjuaga.
            if rule.kind is RuleKind.TECHNIQUE:
                # Una regla de técnica solo toca la etapa a la que pertenece esa
                # técnica: los ajustes del difusor no tienen nada que decir
                # sobre el champú.
                named = str(outcome.get("technique", ""))
                candidate = TECHNIQUES_BY_ID.get(named)
                if candidate is not None and candidate.stage is spec.stage:
                    contributing[rule.id] = evaluated
                continue

            if not spec.accepts_global_attributes:
                continue
            if "product_attributes" in outcome:
                attributes.update(dict(outcome["product_attributes"]))
                contributing[rule.id] = evaluated
            if "add_attributes" in outcome:
                attributes.update(dict(outcome["add_attributes"]))
                contributing[rule.id] = evaluated
            if "amount_modifier" in outcome:
                modifier *= float(outcome["amount_modifier"])
                contributing[rule.id] = evaluated

        return attributes, modifier, contributing

    def _technique_for(
        self,
        stage: TechniqueStage,
        zone_state: ZoneState,
        context: RoutineContext,
        result: EvaluationResult,
    ) -> tuple[Technique | None, tuple[Technique, ...]]:
        """Devuelve la técnica principal del paso y las que la siguen.

        Las técnicas nombradas explícitamente por reglas ganan sobre la
        selección automática: la regla sabe por qué la pide. Cuando hay varias
        para la misma etapa se conservan todas en su orden natural, porque
        difundir y romper el cast no son alternativas, son consecutivas.
        """
        named: list[Technique] = []
        for evaluated in result.active:
            candidate_id = evaluated.rule.outcome.get("technique")
            if not candidate_id:
                continue
            candidate = TECHNIQUES_BY_ID.get(str(candidate_id))
            if candidate is not None and candidate.stage is stage and candidate not in named:
                named.append(candidate)
        if named:
            named.sort(key=lambda t: _STAGE_TECHNIQUE_ORDER.get(t.id, 50))
            return named[0], tuple(named[1:])

        family = zone_state.pattern_family
        if family is None:
            # Sin patrón conocido no se elige técnica: se deja el paso sin ella
            # y la app lo dice, en vez de asumir un patrón.
            return None, ()
        budget = _QUICK_LIMITS.get(context.kind)
        options = techniques_for(stage, family, porosity=zone_state.porosity, max_minutes=budget)
        if not options:
            return None, ()
        goal_keys = {f"goal.{g.value}" for g in context.goals}
        options.sort(
            key=lambda t: (
                -len(goal_keys & set(t.goal_keys)),
                -t.evidence_level.confidence,
                t.minutes,
            )
        )
        return options[0], ()

    def _make_step(
        self,
        order: int,
        instruction: _Instruction,
        context: RoutineContext,
        global_result: EvaluationResult,
    ) -> RoutineStep:
        zones = tuple(z.zone for z in instruction.zones)
        amount = self._amount_for(instruction, context)
        params = self._params_for(instruction, context, global_result)
        explanation = self._explain(instruction, context)
        duration = instruction.spec.default_duration_seconds
        if instruction.technique and instruction.technique.timer_steps:
            duration = sum(instruction.technique.timer_steps) or duration

        return RoutineStep(
            order=order,
            stage=instruction.stage,
            action_key=instruction.action_key,
            zones=zones,
            product_category=instruction.category,
            product_attributes=dict(instruction.attributes),
            amount=amount,
            technique=instruction.technique,
            params=params,
            explanation=explanation,
            duration_seconds=duration,
            follow_up_techniques=instruction.follow_ups,
        )

    def _amount_for(self, instruction: _Instruction, context: RoutineContext) -> Amount | None:
        if instruction.category is None:
            return None
        reference_zone = instruction.zones[0]
        length = reference_zone.length_cm or _median_length(context) or 25.0
        density = reference_zone.density or Density.MEDIUM
        diameter = reference_zone.strand_diameter or StrandDiameter.MEDIUM

        # Si la instrucción cubre todas las zonas del perfil, la cantidad es la
        # total; si cubre solo algunas, se calcula la parte proporcional. La
        # proporción se normaliza sobre las zonas que el perfil tiene de verdad,
        # no sobre el mapa completo: un perfil con 5 zonas cargadas no debe
        # recibir un tercio del champú que necesita.
        covers_all = len(instruction.zones) >= len(context.zones)
        zone_arg = None if covers_all else reference_zone.zone
        amount = compute_amount(
            instruction.category,
            length_cm=length,
            density=density,
            strand_diameter=diameter,
            zone=zone_arg,
            modifier=instruction.modifier,
        )
        if zone_arg is None:
            return amount

        # Suma de la parte proporcional de cada zona cubierta, renormalizada
        # por la cobertura real del perfil.
        covered_ml = 0.0
        for zone_state in instruction.zones:
            covered_ml += compute_amount(
                instruction.category,
                length_cm=zone_state.length_cm or length,
                density=zone_state.density or density,
                strand_diameter=zone_state.strand_diameter or diameter,
                zone=zone_state.zone,
                modifier=instruction.modifier,
            ).ml

        profile_ml = 0.0
        for zone_state in context.zones:
            if instruction.category in _SCALP_ONLY_CATEGORIES and zone_state.zone is Zone.ENDS:
                continue
            profile_ml += compute_amount(
                instruction.category,
                length_cm=zone_state.length_cm or length,
                density=zone_state.density or density,
                strand_diameter=zone_state.strand_diameter or diameter,
                zone=zone_state.zone,
                modifier=instruction.modifier,
            ).ml

        total = compute_amount(
            instruction.category,
            length_cm=length,
            density=density,
            strand_diameter=diameter,
            modifier=instruction.modifier,
        ).ml
        scale = (total / profile_ml) if profile_ml > 0 else 1.0
        final_ml = covered_ml * scale

        reference, multiplier = closest_reference(max(final_ml, 0.05))
        return Amount(
            ml=final_ml,
            reference=reference,
            reference_multiplier=multiplier,
            zone=zone_arg if len(instruction.zones) == 1 else None,
        )

    def _params_for(
        self,
        instruction: _Instruction,
        context: RoutineContext,
        global_result: EvaluationResult,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for evaluated in instruction.rules.values():
            params.update(dict(evaluated.rule.outcome.get("params", {})))
        frequency = instruction.attributes.pop("frequency_hint", None)
        if frequency is not None:
            params["frequency_hint"] = frequency

        if instruction.stage is TechniqueStage.DRY and context.uses_heat:
            temperature = self._heat_temperature(instruction, global_result)
            if temperature is not None:
                params["max_temperature_c"] = temperature
                params["require_heat_protectant"] = True
                params["single_pass"] = True

        if instruction.stage is TechniqueStage.DETANGLE:
            params["direction"] = "ends_to_roots"
            params["state"] = "wet_with_conditioner"
            params["tension"] = "low"

        if instruction.stage is TechniqueStage.APPLY_STYLER:
            params["hair_state"] = "soaking_wet" if _wants_soaking_wet(instruction) else "damp"
            params["section_count"] = _section_count(instruction, context)

        return params

    def _heat_temperature(
        self, instruction: _Instruction, global_result: EvaluationResult
    ) -> int | None:
        """Temperatura por estado de la fibra, nunca una universal (A16)."""
        for evaluated in global_result.active:
            table = evaluated.rule.outcome.get("temperature_by_state")
            if not isinstance(table, Mapping):
                continue
            states = {z.processing for z in instruction.zones if z.processing}
            diameters = {z.strand_diameter for z in instruction.zones if z.strand_diameter}
            candidates: list[int] = []
            for state in states:
                if state is ProcessingState.VIRGIN:
                    suffix = (
                        "fine"
                        if StrandDiameter.FINE in diameters
                        else "coarse"
                        if StrandDiameter.COARSE in diameters
                        else "medium"
                    )
                    key = f"virgin_{suffix}"
                else:
                    key = state.value
                if key in table:
                    candidates.append(int(table[key]))
            if candidates:
                # La zona más frágil manda para toda la instrucción.
                return min(candidates)
        return None

    def _explain(self, instruction: _Instruction, context: RoutineContext) -> Explanation:
        if not instruction.rules:
            return Explanation(
                summary_key=f"{instruction.action_key}.why.default",
                inputs_used=("input.goals",),
                evidence_level="professional_consensus",
                evidence_confidence=0.70,
                personal_confidence=0.0,
                sample_size=0,
                uncertainty_keys=("uncertainty.cold_start",),
            )

        # La regla más sólida es la que encabeza la explicación; las demás se
        # listan como observaciones que también contribuyeron.
        ranked = sorted(instruction.rules.values(), key=lambda e: e.effective_priority, reverse=True)
        lead = ranked[0]
        inputs = tuple(dict.fromkeys(f for e in ranked for f in e.facts_used))
        observations = tuple(e.rule.id for e in ranked)
        uncertainty = tuple(dict.fromkeys(k for e in ranked for k in e.confidence.uncertainty_keys))
        alternatives = tuple(
            a for e in ranked for a in (str(e.rule.outcome.get("suggestion", "")),) if a
        )

        return Explanation(
            summary_key=lead.rule.message_key or f"{instruction.action_key}.why",
            inputs_used=inputs,
            observations=observations,
            evidence_level=lead.rule.evidence_level.value,
            evidence_confidence=lead.confidence.evidence_confidence,
            personal_confidence=lead.confidence.personal_confidence,
            sample_size=lead.confidence.sample_size,
            uncertainty_keys=uncertainty,
            alternatives=alternatives,
            params={
                "mechanism_rule_id": lead.rule.id,
                "personal_direction": lead.confidence.personal_direction,
                "contributing_rules": [e.rule.id for e in ranked],
            },
        )

    def _collect(
        self,
        global_result: EvaluationResult,
        zone_results: Mapping[Zone, EvaluationResult],
        kind: RuleKind,
    ) -> list[Explanation]:
        """Reúne avisos o contenido educativo, sin repetir la misma regla.

        La zona en la que se detectó viaja en `params`: «puntas abiertas en las
        puntas» y «puntas abiertas en la coronilla» no son el mismo hallazgo.
        """
        seen: set[str] = set()
        warnings: list[Explanation] = []
        zone_by_rule: dict[str, list[str]] = {}
        for zone, result in zone_results.items():
            for evaluated in result.of_kind(kind):
                zone_by_rule.setdefault(evaluated.rule.id, []).append(zone.value)
        for result in [global_result, *zone_results.values()]:
            for evaluated in result.of_kind(kind):
                if evaluated.rule.id in seen:
                    continue
                seen.add(evaluated.rule.id)
                warnings.append(
                    evaluated.confidence.as_explanation(
                        summary_key=evaluated.rule.message_key or evaluated.rule.id,
                        inputs_used=evaluated.facts_used,
                        observations=(evaluated.rule.id,),
                        alternatives=(str(evaluated.rule.outcome.get("suggestion", "")),)
                        if evaluated.rule.outcome.get("suggestion")
                        else (),
                        params={
                            "rule_id": evaluated.rule.id,
                            "zones": zone_by_rule.get(evaluated.rule.id, []),
                            "mechanism": evaluated.rule.mechanism,
                        },
                    )
                )
        return warnings

    def _apply_time_budget(
        self, steps: list[RoutineStep], context: RoutineContext
    ) -> tuple[list[RoutineStep], list[str]]:
        """Modos rápidos (A14): recorta por tiempo diciendo qué se sacrifica.

        No se recorta en silencio: la rutina devuelve la razón de cada paso
        omitido para que la persona sepa qué está dejando fuera.
        """
        budget = _QUICK_LIMITS.get(context.kind) or context.available_minutes
        if budget is None:
            return steps, []

        # Lo irrenunciable son los pasos concretos, no la etapa entera: una
        # mascarilla de veinte minutos pertenece a la etapa de acondicionar y
        # es justo lo primero que sobra en una rutina de diez minutos.
        essential_actions = {"step.cleanse", "step.condition", "step.detangle"}
        kept: list[RoutineStep] = []
        skipped: list[str] = []
        spent = 0

        for step in steps:
            cost = step.technique.minutes if step.technique else 2
            cost += sum(t.minutes for t in step.follow_up_techniques)
            if step.duration_seconds:
                cost = max(cost, step.duration_seconds // 60)
            if spent + cost <= budget or step.action_key in essential_actions:
                kept.append(step)
                spent += cost
            else:
                skipped.append(f"skipped.{step.action_key}.time_budget")

        renumbered = [
            RoutineStep(
                order=index + 1,
                stage=s.stage,
                action_key=s.action_key,
                zones=s.zones,
                product_category=s.product_category,
                product_attributes=s.product_attributes,
                amount=s.amount,
                technique=s.technique,
                params=s.params,
                explanation=s.explanation,
                duration_seconds=s.duration_seconds,
                follow_up_techniques=s.follow_up_techniques,
            )
            for index, s in enumerate(kept)
        ]
        return renumbered, skipped


@dataclass
class _Instruction:
    spec: StepSpec
    attributes: dict[str, Any]
    modifier: float
    technique: Technique | None
    follow_ups: tuple[Technique, ...]
    zones: list[ZoneState]
    rules: dict[str, EvaluatedRule]

    @property
    def stage(self) -> TechniqueStage:
        return self.spec.stage

    @property
    def action_key(self) -> str:
        return self.spec.action_key

    @property
    def category(self) -> ProductCategory | None:
        return self.spec.category


def _hashable(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, dict):
        return tuple(sorted(value.items()))
    return value


def _median_length(context: RoutineContext) -> float | None:
    lengths = sorted(z.length_cm for z in context.zones if z.length_cm is not None)
    if not lengths:
        return None
    return lengths[len(lengths) // 2]


def _wants_soaking_wet(instruction: _Instruction) -> bool:
    return any(
        e.rule.outcome.get("technique") == "apply_soaking_wet"
        for e in instruction.rules.values()
    ) or any(z.porosity in {Porosity.HIGH, Porosity.MIXED} for z in instruction.zones)


def _section_count(instruction: _Instruction, context: RoutineContext) -> int:
    """Cuántas secciones para aplicar. Escala con densidad y longitud: aplicar
    en cuatro secciones sobre cabello muy denso deja zonas sin producto."""
    density = instruction.zones[0].density or Density.MEDIUM
    length = instruction.zones[0].length_cm or 25.0
    base = {Density.LOW: 2, Density.MEDIUM: 4, Density.HIGH: 6}[density]
    if length > 40:
        base += 2
    return base
