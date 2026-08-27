"""Conversión entre filas del diario y el modelo del dominio."""

from __future__ import annotations

from collections.abc import Sequence

from ..domain.learning.journal import JournalEntry, ResultRating
from ..models.products import JournalRow

_RATING_FIELDS = ("day1", "day2", "day3", "day4_plus")


def _rating(raw: object) -> ResultRating | None:
    if raw is None:
        return None
    try:
        return ResultRating(int(raw))
    except (ValueError, TypeError):
        return None


def to_domain_entry(row: JournalRow) -> JournalEntry:
    ratings = row.ratings or {}
    weather = row.weather or {}
    return JournalEntry(
        id=row.id,
        date=row.entry_date,
        product_ids=tuple(row.product_ids or ()),
        technique_ids=tuple(row.technique_ids or ()),
        dew_point_c=weather.get("dew_point_c"),
        water_hardness_ppm=weather.get("water_hardness_ppm"),
        amounts_ml=dict(row.amounts_ml or {}),
        rating_day1=_rating(ratings.get("day1")),
        rating_day2=_rating(ratings.get("day2")),
        rating_day3=_rating(ratings.get("day3")),
        rating_day4_plus=_rating(ratings.get("day4_plus")),
        notes=row.notes,
        experiment_arm_id=row.experiment_arm_id,
    )


def to_domain_entries(rows: Sequence[JournalRow]) -> list[JournalEntry]:
    return [to_domain_entry(row) for row in rows]
