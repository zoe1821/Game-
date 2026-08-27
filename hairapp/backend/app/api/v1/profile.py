"""Perfil capilar, mapa de zonas y objetivos."""

from __future__ import annotations

from fastapi import APIRouter, status

from ...core.errors import NotFound, ValidationFailed
from ...domain.hair.attributes import CurlPattern
from ...domain.hair.zones import ALL_ZONES, Zone
from ...domain.routine.generator import Goal as GoalEnum
from ...models.hair import Goal
from ...schemas.common import MeasuredOut
from ...schemas.hair import (
    DeepOnboardingSectionIn,
    EssentialOnboardingIn,
    GoalsIn,
    ProfileOut,
    ZoneCorrectionIn,
    ZoneOut,
)
from ...services.profile_service import (
    MEASURABLE_FIELDS,
    apply_estimates,
    compute_completeness,
    ensure_zones,
    get_zone,
    set_user_value,
)
from ..deps import CurrentProfile, DbSession

router = APIRouter(prefix="/profile", tags=["profile"])

#: Secciones válidas de la profundización opcional (B3).
DEEP_SECTIONS = frozenset(
    {"hair_now", "chemical_history", "mechanical_history", "products", "sleep", "environment"}
)


def _zone_out(zone_row) -> ZoneOut:
    measurements = {
        field: MeasuredOut(
            value=payload["value"],
            confidence=payload["confidence"],
            source=payload["source"],
            observed_at=payload.get("observed_at"),
            notes=payload.get("notes"),
        )
        for field, payload in zone_row.measurements.items()
    }
    return ZoneOut(
        zone=zone_row.zone.value,
        label_key=zone_row.zone.label_key,
        measurements=measurements,
        damage_signs=list(zone_row.damage_signs),
        notes=zone_row.notes,
        completeness=round(len(measurements) / len(MEASURABLE_FIELDS), 3),
    )


def _profile_out(profile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        depth_level=profile.depth_level,
        completeness=profile.completeness,
        onboarding_essential_done=profile.onboarding_essential_done,
        wash_frequency_days=profile.wash_frequency_days,
        country=profile.country,
        water_hardness_ppm=profile.water_hardness_ppm,
        uses_heat=profile.uses_heat,
        owns_diffuser=profile.owns_diffuser,
        protective_style=profile.protective_style,
        goals=[g.kind for g in sorted(profile.goals, key=lambda g: g.priority)],
        zones=[_zone_out(z) for z in sorted(profile.zones, key=lambda z: z.zone.value)],
    )


@router.get("", response_model=ProfileOut)
def read_profile(profile: CurrentProfile, session: DbSession) -> ProfileOut:
    ensure_zones(session, profile)
    return _profile_out(profile)


@router.post("/onboarding/essential", response_model=ProfileOut)
def essential_onboarding(
    payload: EssentialOnboardingIn, profile: CurrentProfile, session: DbSession
) -> ProfileOut:
    """Onboarding mínimo: lo indispensable para empezar (B3).

    Se guarda como estimación con fuente inferida y confianza moderada, nunca
    como certeza: son respuestas rápidas, no un análisis.
    """
    from datetime import date

    from ...domain.common import Measured, Source

    try:
        goal = GoalEnum(payload.primary_goal)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_goal", goal=payload.primary_goal) from exc

    profile.wash_frequency_days = payload.wash_frequency_days
    profile.country = payload.country
    profile.onboarding_essential_done = True

    zones = ensure_zones(session, profile)
    today = date.today()

    if payload.dominant_pattern:
        try:
            pattern = CurlPattern(payload.dominant_pattern)
        except ValueError as exc:
            raise ValidationFailed(
                "error.unknown_pattern", pattern=payload.dominant_pattern
            ) from exc
        estimate = Measured(pattern, Source.INFERRED, 0.45, today, notes="essential_onboarding")
        for zone_row in zones:
            apply_estimates(session, zone_row, {"pattern": estimate})

    if payload.approximate_length_cm is not None:
        length = Measured(
            float(payload.approximate_length_cm), Source.USER, 1.0, today
        )
        for zone_row in zones:
            apply_estimates(session, zone_row, {"length_cm": length})

    existing = {g.kind for g in profile.goals}
    if goal.value not in existing:
        session.add(Goal(profile_id=profile.id, kind=goal.value, priority=1))
        session.flush()
        session.refresh(profile)

    profile.completeness = compute_completeness(profile)
    session.add(profile)
    return _profile_out(profile)


@router.post("/onboarding/deep", response_model=ProfileOut)
def deep_onboarding(
    payload: DeepOnboardingSectionIn, profile: CurrentProfile, session: DbSession
) -> ProfileOut:
    """Profundización opcional por secciones (B3).

    Nunca es obligatoria y no bloquea nada: solo sube la completitud del perfil
    y, con ella, la calidad de las estimaciones.
    """
    if payload.section not in DEEP_SECTIONS:
        raise ValidationFailed("error.unknown_section", section=payload.section)

    habits = dict(profile.habits or {})
    habits[payload.section] = payload.answers
    profile.habits = habits

    if payload.section == "environment":
        hardness = payload.answers.get("water_hardness_ppm")
        if hardness is not None:
            profile.water_hardness_ppm = float(hardness)
    if payload.section == "products":
        profile.uses_heat = bool(payload.answers.get("uses_heat", profile.uses_heat))
        profile.owns_diffuser = bool(payload.answers.get("owns_diffuser", profile.owns_diffuser))

    profile.completeness = compute_completeness(profile)
    session.add(profile)
    return _profile_out(profile)


@router.put("/depth-level", response_model=ProfileOut)
def set_depth_level(level: str, profile: CurrentProfile, session: DbSession) -> ProfileOut:
    """Nivel de profundidad de la interfaz (B3).

    Las funciones avanzadas están ocultas por defecto: se activan aquí.
    """
    if level not in {"basic", "intermediate", "advanced"}:
        raise ValidationFailed("error.unknown_depth_level", level=level)
    profile.depth_level = level
    session.add(profile)
    return _profile_out(profile)


@router.put("/goals", response_model=ProfileOut)
def set_goals(payload: GoalsIn, profile: CurrentProfile, session: DbSession) -> ProfileOut:
    """Objetivos múltiples y priorizados (A8). El orden es la prioridad."""
    parsed = []
    for kind in payload.goals:
        try:
            parsed.append(GoalEnum(kind))
        except ValueError as exc:
            raise ValidationFailed("error.unknown_goal", goal=kind) from exc

    for goal_row in list(profile.goals):
        session.delete(goal_row)
    session.flush()

    for priority, goal in enumerate(parsed, start=1):
        session.add(Goal(profile_id=profile.id, kind=goal.value, priority=priority))
    session.flush()
    session.refresh(profile)

    profile.completeness = compute_completeness(profile)
    session.add(profile)
    return _profile_out(profile)


@router.get("/zones", response_model=list[ZoneOut])
def list_zones(profile: CurrentProfile, session: DbSession) -> list[ZoneOut]:
    zones = ensure_zones(session, profile)
    return [_zone_out(z) for z in sorted(zones, key=lambda z: z.zone.value)]


@router.put("/zones/{zone_value}", response_model=ZoneOut)
def correct_zone(
    zone_value: str,
    payload: ZoneCorrectionIn,
    profile: CurrentProfile,
    session: DbSession,
) -> ZoneOut:
    """Corrección manual de cualquier estimación (A1.4).

    A partir de aquí el valor es definitivo: ningún análisis posterior lo
    sobrescribe.
    """
    try:
        zone = Zone(zone_value)
    except ValueError as exc:
        raise NotFound("zone", zone=zone_value) from exc

    zone_row = get_zone(session, profile.id, zone)
    if zone_row is None:
        ensure_zones(session, profile)
        zone_row = get_zone(session, profile.id, zone)
    if zone_row is None:
        raise NotFound("zone", zone=zone_value)

    if payload.field not in MEASURABLE_FIELDS:
        raise ValidationFailed("error.field_not_measurable", field=payload.field)

    set_user_value(session, zone_row, payload.field, payload.value)
    profile.completeness = compute_completeness(profile)
    session.add(profile)
    return _zone_out(zone_row)


@router.put("/zones/{zone_value}/damage", response_model=ZoneOut)
def set_zone_damage(
    zone_value: str,
    signs: list[str],
    profile: CurrentProfile,
    session: DbSession,
) -> ZoneOut:
    from ...domain.hair.attributes import DamageSign

    try:
        zone = Zone(zone_value)
    except ValueError as exc:
        raise NotFound("zone", zone=zone_value) from exc

    valid = {s.value for s in DamageSign}
    unknown = [s for s in signs if s not in valid]
    if unknown:
        raise ValidationFailed("error.unknown_damage_sign", signs=unknown)

    zone_row = get_zone(session, profile.id, zone)
    if zone_row is None:
        raise NotFound("zone", zone=zone_value)
    zone_row.damage_signs = signs
    session.add(zone_row)
    return _zone_out(zone_row)


@router.get("/zones/catalog", status_code=status.HTTP_200_OK)
def zone_catalog() -> list[dict[str, str]]:
    """El mapa de zonas disponible para la UI, con sus claves i18n."""
    return [{"zone": z.value, "label_key": z.label_key} for z in ALL_ZONES]
