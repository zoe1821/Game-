"""Generación de rutinas y consulta de técnicas."""

from __future__ import annotations

from fastapi import APIRouter

from ...core.errors import ValidationFailed
from ...domain.climate.weather import Weather, forecast
from ...domain.routine.generator import RoutineKind
from ...domain.routine.techniques import TECHNIQUES
from ...schemas.hair import RoutineOut, RoutineRequestIn
from ...services.routine_service import generate_for_profile
from ..deps import CurrentProfile, DbSession

router = APIRouter(prefix="/routines", tags=["routines"])


@router.post("/generate", response_model=RoutineOut)
def generate(
    payload: RoutineRequestIn, profile: CurrentProfile, session: DbSession
) -> RoutineOut:
    try:
        kind = RoutineKind(payload.kind)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_routine_kind", kind=payload.kind) from exc

    weather: dict[str, float] = {}
    if payload.temperature_c is not None and payload.relative_humidity is not None:
        conditions = Weather(
            temperature_c=payload.temperature_c,
            relative_humidity=payload.relative_humidity,
            uv_index=payload.uv_index,
        )
        weather = {
            "temperature_c": conditions.temperature_c,
            "relative_humidity": conditions.relative_humidity,
            "dew_point_c": conditions.dew_point_c,
        }
        if payload.uv_index is not None:
            weather["uv_index"] = payload.uv_index

    routine = generate_for_profile(
        session,
        profile,
        kind=kind,
        weather=weather,
        available_minutes=payload.available_minutes,
        scalp_observations=payload.scalp_observations,
        scalp_referral_signs=payload.scalp_referral_signs,
    )
    return RoutineOut.model_validate(routine.as_dict())


@router.get("/techniques", tags=["education"])
def list_techniques(profile: CurrentProfile) -> list[dict[str, object]]:
    """Biblioteca de técnicas (A9), con su nivel de evidencia visible.

    En nivel de profundidad básico se ocultan las avanzadas (B3): no se
    esconden por capricho, es que una técnica de 45 minutos no es un buen
    primer contacto.
    """
    show_advanced = profile.depth_level in {"intermediate", "advanced"}
    return [
        {
            "id": t.id,
            "stage": t.stage.value,
            "name_key": t.name_key,
            "description_key": t.description_key,
            "evidence_level": t.evidence_level.value,
            "evidence_label_key": t.evidence_level.label_key,
            "difficulty": t.difficulty.value,
            "minutes": t.minutes,
            "goal_keys": list(t.goal_keys),
            "step_keys": list(t.step_keys),
            "timer_steps": list(t.timer_steps),
            "caution_keys": list(t.caution_keys),
            "not_for_keys": list(t.not_for_keys),
        }
        for t in TECHNIQUES
        if show_advanced or t.difficulty.value != "advanced"
    ]


@router.get("/weather-forecast", tags=["weather"])
def weather_forecast(
    temperature_c: float,
    relative_humidity: float,
    profile: CurrentProfile,
    uv_index: float | None = None,
    wind_kph: float | None = None,
) -> dict[str, object]:
    """Pronóstico capilar (A12).

    Usa punto de rocío, no humedad relativa: 80 % a 5 °C y 80 % a 28 °C
    describen cantidades de agua muy distintas.
    """
    porosities = [
        payload["value"]
        for zone in profile.zones
        for field, payload in zone.measurements.items()
        if field == "porosity"
    ]
    dominant = max(set(porosities), key=porosities.count) if porosities else None

    conditions = Weather(
        temperature_c=temperature_c,
        relative_humidity=relative_humidity,
        uv_index=uv_index,
        wind_kph=wind_kph,
    )
    return forecast(conditions, porosity=dominant).as_dict()
