from __future__ import annotations

from datetime import date

from pydantic import Field, field_validator

from .common import ApiModel

VALID_RATING_KEYS = frozenset({"day1", "day2", "day3", "day4_plus"})


class RatingsIn(ApiModel):
    """Valoraciones por día. Escala 1-4 corta a propósito: una de 1 a 10
    sugiere una precisión que nadie tiene al valorar su propio pelo."""

    ratings: dict[str, int] = Field(default_factory=dict)

    @field_validator("ratings")
    @classmethod
    def _check(cls, value: dict[str, int]) -> dict[str, int]:
        unknown = set(value) - VALID_RATING_KEYS
        if unknown:
            raise ValueError(f"claves de valoración desconocidas: {sorted(unknown)}")
        for rating in value.values():
            if rating not in (1, 2, 3, 4):
                raise ValueError("las valoraciones van de 1 a 4")
        return value


class JournalEntryIn(RatingsIn):
    entry_date: date
    product_ids: list[str] = Field(default_factory=list)
    technique_ids: list[str] = Field(default_factory=list)
    amounts_ml: dict[str, float] = Field(default_factory=dict)
    weather: dict[str, float] = Field(default_factory=dict)
    notes: str | None = None
    experiment_arm_id: str | None = None


class JournalEntryOut(ApiModel):
    id: str
    date: str
    product_ids: list[str] = Field(default_factory=list)
    technique_ids: list[str] = Field(default_factory=list)
    amounts_ml: dict[str, float] = Field(default_factory=dict)
    weather: dict[str, float] = Field(default_factory=dict)
    ratings: dict[str, int] = Field(default_factory=dict)
    notes: str | None = None
    experiment_arm_id: str | None = None
    longevity_days: int = 0


class InventoryItemIn(ApiModel):
    product_id: str | None = None
    custom_name: str | None = None
    custom_category: str | None = None
    custom_inci: str | None = None
    opened_at: date | None = None
    pao_months: int | None = None
    notes: str | None = None


class MatchRequestIn(ApiModel):
    category: str
    wanted_attributes: dict[str, object] = Field(default_factory=dict)


class IngredientScanIn(ApiModel):
    inci: str = Field(min_length=3)


class ExperimentArmIn(ApiModel):
    label_key: str
    product_ids: list[str] = Field(default_factory=list)
    technique_ids: list[str] = Field(default_factory=list)


class ExperimentIn(ApiModel):
    question_key: str
    arms: list[ExperimentArmIn] = Field(min_length=2, max_length=4)
    controlled_variables: list[str] = Field(default_factory=list)
    target_repetitions_per_arm: int = Field(default=4, ge=2, le=12)
    is_premium: bool = False
