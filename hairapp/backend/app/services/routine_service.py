"""Genera una rutina a partir del estado guardado del perfil."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.confidence.engine import PersonalEvidence
from ..domain.hair.attributes import (
    CurlPattern,
    Density,
    Porosity,
    ProcessingState,
    StrandDiameter,
)
from ..domain.learning.journal import JournalEntry
from ..domain.routine.generator import (
    GeneratedRoutine,
    Goal,
    RoutineContext,
    RoutineKind,
    ZoneState,
)
from ..models.hair import HairProfile
from ..models.products import JournalRow
from .engine import get_routine_generator
from .journal_service import to_domain_entries
from .profile_service import zone_states

_ENUM_FIELDS: Mapping[str, Any] = {
    "pattern": CurlPattern,
    "porosity": Porosity,
    "density": Density,
    "strand_diameter": StrandDiameter,
    "processing": ProcessingState,
}


def build_zone_states(profile: HairProfile) -> list[ZoneState]:
    states: list[ZoneState] = []
    for flat in zone_states(profile):
        kwargs: dict[str, Any] = {
            "zone": flat["zone"],
            "damage_signs": flat.get("damage_signs", ()),
            "confidence_by_field": flat.get("confidence_by_field", {}),
        }
        for field, enum_type in _ENUM_FIELDS.items():
            raw = flat.get(field)
            if raw is not None:
                try:
                    kwargs[field] = enum_type(raw)
                except ValueError:
                    # Un valor guardado que ya no existe en el enum no rompe el
                    # perfil entero: se ignora ese campo y el resto sigue.
                    continue
        for field in ("length_cm", "frizz_level"):
            if flat.get(field) is not None:
                kwargs[field] = float(flat[field])
        states.append(ZoneState(**kwargs))
    return states


def build_context(
    profile: HairProfile,
    *,
    kind: RoutineKind = RoutineKind.WASH_DAY,
    weather: Mapping[str, Any] | None = None,
    available_minutes: int | None = None,
    scalp_observations: Sequence[str] = (),
    scalp_referral_signs: Sequence[str] = (),
) -> RoutineContext:
    goals = []
    for goal_row in sorted(profile.goals, key=lambda g: g.priority):
        try:
            goals.append(Goal(goal_row.kind))
        except ValueError:
            continue

    habits = profile.habits or {}
    return RoutineContext(
        zones=build_zone_states(profile),
        goals=goals,
        kind=kind,
        weather=dict(weather or {}),
        water_hardness_ppm=profile.water_hardness_ppm,
        scalp_observations=tuple(scalp_observations),
        scalp_referral_signs=tuple(scalp_referral_signs),
        uses_heat=profile.uses_heat,
        owns_diffuser=profile.owns_diffuser,
        uses_cowash=bool(habits.get("uses_cowash")),
        protein_frequency_per_month=int(habits.get("protein_frequency_per_month", 0) or 0),
        reports_stiff_hair=bool(habits.get("reports_stiff_hair")),
        protective_style=profile.protective_style,
        available_minutes=available_minutes,
    )


def personal_evidence_lookup(entries: Sequence[JournalEntry]):
    """Construye el buscador de historial que alimenta `personal_confidence`.

    La correspondencia entre una regla y el historial es aproximada por
    diseño: se emparejan por las etiquetas de la regla contra lo registrado.
    Cuando no hay correspondencia devuelve historial vacío, que es lo honesto:
    confianza personal 0 y arranque en frío declarado.
    """
    by_technique: dict[str, list[JournalEntry]] = {}
    for entry in entries:
        for technique in entry.technique_ids:
            by_technique.setdefault(technique, []).append(entry)

    def lookup(rule_id: str) -> PersonalEvidence:
        matching = [
            entry
            for technique, group in by_technique.items()
            if technique in rule_id
            for entry in group
        ]
        if not matching:
            return PersonalEvidence()
        supporting = sum(1 for e in matching if (e.mean_rating or 0) >= 3.0)
        return PersonalEvidence(
            supporting=supporting,
            contradicting=len(matching) - supporting,
            most_recent=max(e.date for e in matching),
            controlled=any(e.is_controlled for e in matching),
        )

    return lookup


def generate_for_profile(
    session: Session,
    profile: HairProfile,
    *,
    kind: RoutineKind = RoutineKind.WASH_DAY,
    weather: Mapping[str, Any] | None = None,
    available_minutes: int | None = None,
    scalp_observations: Sequence[str] = (),
    scalp_referral_signs: Sequence[str] = (),
    today: date | None = None,
) -> GeneratedRoutine:
    rows = (
        session.execute(
            select(JournalRow)
            .where(JournalRow.profile_id == profile.id)
            .order_by(JournalRow.entry_date.desc())
            .limit(60)
        )
        .scalars()
        .all()
    )
    entries = to_domain_entries(rows)

    context = build_context(
        profile,
        kind=kind,
        weather=weather,
        available_minutes=available_minutes,
        scalp_observations=scalp_observations,
        scalp_referral_signs=scalp_referral_signs,
    )
    return get_routine_generator().generate(
        context, personal=personal_evidence_lookup(entries), today=today
    )
