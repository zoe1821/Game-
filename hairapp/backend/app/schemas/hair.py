from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import ApiModel, ExplanationOut, MeasuredOut


class ZoneOut(ApiModel):
    zone: str
    label_key: str
    measurements: dict[str, MeasuredOut] = Field(default_factory=dict)
    damage_signs: list[str] = Field(default_factory=list)
    notes: str | None = None
    completeness: float = 0.0


class ZoneCorrectionIn(ApiModel):
    """Corrección manual de una estimación (A1.4).

    Cualquier campo estimable se puede corregir, y la corrección es definitiva.
    """

    field: str
    value: Any


class ProfileOut(ApiModel):
    id: str
    depth_level: str
    completeness: float
    onboarding_essential_done: bool
    wash_frequency_days: float | None = None
    country: str | None = None
    water_hardness_ppm: float | None = None
    uses_heat: bool = False
    owns_diffuser: bool = False
    protective_style: str = "none"
    goals: list[str] = Field(default_factory=list)
    zones: list[ZoneOut] = Field(default_factory=list)


class EssentialOnboardingIn(ApiModel):
    """Onboarding mínimo (B3): menos de 3 minutos, lo indispensable para usar
    la app. Todo lo demás es profundización opcional."""

    dominant_pattern: str | None = None
    approximate_length_cm: float | None = None
    wash_frequency_days: float | None = None
    primary_goal: str
    country: str | None = None
    is_chemically_processed: bool = False


class DeepOnboardingSectionIn(ApiModel):
    """Una sección de profundización. Se completan cuando la persona quiera."""

    section: str
    answers: dict[str, Any]


class GoalsIn(ApiModel):
    goals: list[str] = Field(min_length=1, max_length=5)
    """Priorizados: el orden de la lista es la prioridad."""


class RoutineStepOut(ApiModel):
    order: int
    stage: str
    action_key: str
    zones: list[str]
    product_category: str | None = None
    product_attributes: dict[str, Any] = Field(default_factory=dict)
    amount: dict[str, Any] | None = None
    technique_id: str | None = None
    technique_steps: list[str] = Field(default_factory=list)
    follow_up_technique_ids: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: int | None = None
    explanation: ExplanationOut


class RoutineOut(ApiModel):
    kind: str
    halted: bool = False
    halt_block_key: str | None = None
    total_minutes: int = 0
    steps: list[RoutineStepOut] = Field(default_factory=list)
    warnings: list[ExplanationOut] = Field(default_factory=list)
    education: list[ExplanationOut] = Field(default_factory=list)
    skipped_reason_keys: list[str] = Field(default_factory=list)


class RoutineRequestIn(ApiModel):
    kind: str = "wash_day"
    available_minutes: int | None = None
    temperature_c: float | None = None
    relative_humidity: float | None = None
    uv_index: float | None = None
    scalp_observations: list[str] = Field(default_factory=list)
    scalp_referral_signs: list[str] = Field(default_factory=list)
