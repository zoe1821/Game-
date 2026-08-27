from app.domain.hair.attributes import (
    CurlPattern,
    Density,
    Porosity,
    ProcessingState,
    StrandDiameter,
)
from app.domain.hair.zones import Zone
from app.domain.routine.amounts import ProductCategory
from app.domain.routine.generator import (
    Goal,
    RoutineContext,
    RoutineGenerator,
    RoutineKind,
    ZoneState,
)
from app.domain.routine.techniques import TechniqueStage


def _mixed_head() -> list[ZoneState]:
    """Una cabeza real: coronilla decolorada 3a fina, nuca virgen 3c densa."""
    zones = [
        ZoneState(
            z,
            pattern=CurlPattern.CURLY_3A,
            porosity=Porosity.HIGH,
            density=Density.MEDIUM,
            strand_diameter=StrandDiameter.FINE,
            processing=ProcessingState.BLEACHED,
            length_cm=30,
        )
        for z in (Zone.CROWN, Zone.BACK_CROWN)
    ]
    zones += [
        ZoneState(
            z,
            pattern=CurlPattern.CURLY_3C,
            porosity=Porosity.MEDIUM,
            density=Density.HIGH,
            strand_diameter=StrandDiameter.MEDIUM,
            processing=ProcessingState.VIRGIN,
            length_cm=35,
        )
        for z in (Zone.NAPE, Zone.OCCIPITAL)
    ]
    zones.append(
        ZoneState(
            Zone.ENDS,
            pattern=CurlPattern.CURLY_3B,
            porosity=Porosity.HIGH,
            density=Density.MEDIUM,
            strand_diameter=StrandDiameter.FINE,
            processing=ProcessingState.BLEACHED,
            length_cm=35,
            damage_signs=("split_ends", "breakage"),
        )
    )
    return zones


def test_zones_with_different_needs_get_different_instructions(engine) -> None:
    """El primer pilar del producto: una cabeza no es un tipo (A4)."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION])
    )
    cleanse = [s for s in routine.steps if s.action_key == "step.cleanse"]
    assert len(cleanse) >= 2, "la coronilla porosa y la nuca virgen no pueden compartir champú"
    porous_step = next(s for s in cleanse if Zone.CROWN in s.zones)
    assert porous_step.product_attributes["surfactant_strength"] == ["mild", "medium"]


def test_every_step_carries_a_full_explanation(engine) -> None:
    """A21: nada se recomienda sin poder responder «¿por qué esto?»."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION])
    )
    assert routine.steps
    for step in routine.steps:
        explanation = step.explanation
        assert explanation.summary_key
        assert explanation.evidence_level
        assert 0.0 <= explanation.evidence_confidence <= 1.0
        assert 0.0 <= explanation.personal_confidence <= 1.0
        assert explanation.sample_size >= 0


def test_instructions_are_specific_not_vague(engine) -> None:
    """A8: nada de «aplica producto y define»."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION], owns_diffuser=True)
    )
    styling = [s for s in routine.steps if s.stage is TechniqueStage.APPLY_STYLER]
    assert styling
    for step in styling:
        assert step.amount is not None and step.amount.ml > 0
        assert step.amount.reference.key, "toda cantidad lleva referencia visual (A10)"
        assert step.params.get("hair_state") in {"soaking_wet", "damp"}
        assert step.params.get("section_count", 0) > 0

    detangle = next(s for s in routine.steps if s.stage is TechniqueStage.DETANGLE)
    assert detangle.params["direction"] == "ends_to_roots"
    assert detangle.params["tension"] == "low"


def test_heat_temperature_follows_the_most_fragile_zone(engine) -> None:
    """A16: no existe una temperatura universal segura."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION], uses_heat=True)
    )
    dry = next(s for s in routine.steps if s.stage is TechniqueStage.DRY)
    # La coronilla decolorada manda: 150 °C, no los 185 °C del cabello virgen.
    assert dry.params["max_temperature_c"] == 150
    assert dry.params["require_heat_protectant"] is True


def test_referral_signal_produces_no_routine_at_all(engine) -> None:
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(
            zones=_mixed_head(),
            goals=[Goal.DEFINITION],
            scalp_referral_signs=("open_wound",),
        )
    )
    assert routine.halted
    assert routine.steps == ()
    assert routine.halt_block_key == "safety.referral_block"


def test_quick_mode_declares_what_it_sacrifices(engine) -> None:
    """A14: recortar por tiempo nunca ocurre en silencio."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION], kind=RoutineKind.QUICK_10)
    )
    assert routine.skipped_reason_keys
    kept = {s.action_key for s in routine.steps}
    assert "step.cleanse" in kept and "step.condition" in kept


def test_optional_steps_only_appear_when_a_rule_asks_for_them(engine) -> None:
    generator = RoutineGenerator(engine)
    plain = [
        ZoneState(
            Zone.CROWN,
            pattern=CurlPattern.WAVY_2B,
            porosity=Porosity.MEDIUM,
            density=Density.MEDIUM,
            strand_diameter=StrandDiameter.MEDIUM,
            processing=ProcessingState.VIRGIN,
            length_cm=25,
        )
    ]
    routine = generator.generate(RoutineContext(zones=plain, goals=[Goal.DEFINITION]))
    actions = {s.action_key for s in routine.steps}
    assert "step.clarify" not in actions, "no se clarifica sin motivo"
    assert "step.deep_condition" not in actions, "no se añade mascarilla por si acaso"


def test_hard_water_produces_a_chelating_step_distinct_from_clarifying(engine) -> None:
    """A12: clarificar y quelar no son lo mismo y no se sustituyen."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(
            zones=_mixed_head(),
            goals=[Goal.DEFINITION],
            water_hardness_ppm=260,
            scalp_observations=("buildup",),
        )
    )
    actions = [s.action_key for s in routine.steps]
    assert "step.chelate" in actions
    assert "step.clarify" in actions
    chelate = next(s for s in routine.steps if s.action_key == "step.chelate")
    assert chelate.product_attributes["chelating"] is True
    assert chelate.params["frequency_hint"] == "monthly"


def test_shampoo_is_never_applied_to_the_ends(engine) -> None:
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION])
    )
    for step in routine.steps:
        if step.product_category is ProductCategory.SHAMPOO:
            assert Zone.ENDS not in step.zones


def test_hold_level_does_not_leak_into_leave_in(engine) -> None:
    """Una regla que pide fijación para el gel no puede fijar el sin-aclarado."""
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION])
    )
    for step in routine.steps:
        if step.action_key == "step.leave_in":
            assert "hold_level" not in step.product_attributes


def test_visible_damage_surfaces_as_education_with_its_zone(engine) -> None:
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DAMAGE_RECOVERY])
    )
    keys = {e.summary_key for e in routine.education}
    assert "rule.damage.split_ends" in keys
    entry = next(e for e in routine.education if e.summary_key == "rule.damage.split_ends")
    assert "ends" in entry.params["zones"]


def test_drying_techniques_are_ordered_not_alternatives(engine) -> None:
    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(
            zones=_mixed_head(), goals=[Goal.DEFINITION, Goal.VOLUME], owns_diffuser=True
        )
    )
    dry = next(s for s in routine.steps if s.stage is TechniqueStage.DRY)
    chain = [dry.technique.id, *[t.id for t in dry.follow_up_techniques]]
    assert chain.index("diffusing") < chain.index("scrunch_out_the_crunch")


def test_routine_is_serialisable(engine) -> None:
    import json

    generator = RoutineGenerator(engine)
    routine = generator.generate(
        RoutineContext(zones=_mixed_head(), goals=[Goal.DEFINITION])
    )
    payload = json.dumps(routine.as_dict())
    assert "explanation" in payload
