"""Diario de wash day, aprendizaje personalizado y arranque en frío."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from ...core.errors import NotFound
from ...db.session import TransactionalRoute
from ...domain.common import Measured, Source
from ...domain.hair.attributes import Density, Porosity, StrandDiameter
from ...domain.learning.cold_start import guidance
from ...domain.learning.journal import analyse_journal
from ...models.products import JournalRow
from ...models.user import ConsentPurpose
from ...schemas.journal import JournalEntryIn, JournalEntryOut, RatingsIn
from ...services.journal_service import to_domain_entries, to_domain_entry
from ..deps import CurrentProfile, CurrentUser, DbSession

router = APIRouter(prefix="/journal", tags=["journal"], route_class=TransactionalRoute)


@router.get("", response_model=list[JournalEntryOut])
def list_entries(
    profile: CurrentProfile, session: DbSession, limit: int = 50
) -> list[JournalEntryOut]:
    rows = (
        session.execute(
            select(JournalRow)
            .where(JournalRow.profile_id == profile.id)
            .order_by(JournalRow.entry_date.desc())
            .limit(min(limit, 200))
        )
        .scalars()
        .all()
    )
    return [_entry_out(row) for row in rows]


@router.post("", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: JournalEntryIn, profile: CurrentProfile, session: DbSession
) -> JournalEntryOut:
    row = JournalRow(
        profile_id=profile.id,
        entry_date=payload.entry_date,
        product_ids=payload.product_ids,
        technique_ids=payload.technique_ids,
        amounts_ml=payload.amounts_ml,
        weather=payload.weather,
        ratings=payload.ratings,
        notes=payload.notes,
        experiment_arm_id=payload.experiment_arm_id,
    )
    session.add(row)
    session.flush()
    return _entry_out(row)


@router.put("/{entry_id}/ratings", response_model=JournalEntryOut)
def update_ratings(
    entry_id: str, payload: RatingsIn, profile: CurrentProfile, session: DbSession
) -> JournalEntryOut:
    """Registrar los días 2, 3 y 4+ es lo que hace útil el diario.

    Un resultado que se ve bien el día 1 y se deshace el día 2 no es el mismo
    resultado, y sin ese dato el twin no puede aprender la duración.
    """
    row = session.get(JournalRow, entry_id)
    if row is None or row.profile_id != profile.id:
        raise NotFound("journal_entry", entry_id=entry_id)

    merged = dict(row.ratings or {})
    merged.update(payload.ratings)
    row.ratings = merged
    session.add(row)
    session.flush()
    return _entry_out(row)


def _entry_out(row: JournalRow) -> JournalEntryOut:
    return JournalEntryOut(
        id=row.id,
        date=row.entry_date.isoformat(),
        product_ids=list(row.product_ids or ()),
        technique_ids=list(row.technique_ids or ()),
        amounts_ml=dict(row.amounts_ml or {}),
        weather=dict(row.weather or {}),
        ratings=dict(row.ratings or {}),
        notes=row.notes,
        experiment_arm_id=row.experiment_arm_id,
        longevity_days=to_domain_entry(row).longevity_days,
    )


@router.get("/insights")
def insights(profile: CurrentProfile, session: DbSession) -> dict[str, object]:
    """Patrones observados en el historial (A13).

    Puede devolver lista vacía, y eso no es un fallo: significa que todavía no
    hay datos para concluir, que es exactamente lo que hay que decir.
    """
    rows = (
        session.execute(select(JournalRow).where(JournalRow.profile_id == profile.id))
        .scalars()
        .all()
    )
    entries = to_domain_entries(rows)
    findings = analyse_journal(entries)
    return {
        "entry_count": len(entries),
        "findings": [f.as_dict() for f in findings],
        "has_enough_data": bool(findings),
        "message_key": (
            "learning.findings_available" if findings else "learning.still_learning_about_you"
        ),
    }


@router.get("/cold-start")
def cold_start(
    profile: CurrentProfile, user: CurrentUser, session: DbSession
) -> dict[str, object]:
    """Qué puede ofrecer la app mientras todavía no conoce a esta persona (B2)."""
    entry_count = len(
        session.execute(
            select(JournalRow.id).where(JournalRow.profile_id == profile.id)
        )
        .scalars()
        .all()
    )

    values: dict[str, tuple[str, float]] = {}
    for zone in profile.zones:
        for field, payload in zone.measurements.items():
            if field in {"porosity", "density", "strand_diameter", "pattern"}:
                values.setdefault(field, (payload["value"], payload["confidence"]))

    def measured(field: str, enum_type):
        raw = values.get(field)
        if raw is None:
            return None
        try:
            return Measured(enum_type(raw[0]), Source.INFERRED, min(raw[1], 0.8))
        except ValueError:
            return None

    pattern_value = values.get("pattern")
    result = guidance(
        entry_count=entry_count,
        porosity=measured("porosity", Porosity),
        density=measured("density", Density),
        strand_diameter=measured("strand_diameter", StrandDiameter),
        pattern_family=pattern_value[0][0] if pattern_value else None,
        reference_profiles=(),
        consented_to_reference_profiles=user.has_consent(ConsentPurpose.ANONYMOUS_AGGREGATE),
    )
    return result.as_dict()
