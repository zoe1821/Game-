"""Hair Digital Twin y experimentos personales."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from ...core.errors import Forbidden, NotFound, ValidationFailed
from ...db.base import utcnow
from ...domain.experiments.engine import Experiment, ExperimentArm, read_experiment
from ...domain.learning.journal import analyse_journal
from ...domain.twin.model import build_twin
from ...domain.twin.projection import Scenario, project
from ...models.products import ExperimentArmRow, ExperimentRow, JournalRow, TwinSnapshot
from ...schemas.journal import ExperimentIn
from ...services.journal_service import to_domain_entries
from ..deps import CurrentProfile, DbSession

router = APIRouter(prefix="/twin", tags=["twin"])

#: Límite del tier gratuito (docs/02-MONETIZATION.md §2): un experimento activo.
#: Se cobra por profundidad analítica, nunca por acceso básico ni por los datos
#: que la persona ya generó.
FREE_TIER_ACTIVE_EXPERIMENTS = 1


def _entries(session: DbSession, profile_id: str):
    rows = (
        session.execute(select(JournalRow).where(JournalRow.profile_id == profile_id))
        .scalars()
        .all()
    )
    return rows, to_domain_entries(rows)


@router.get("")
def read_twin(profile: CurrentProfile, session: DbSession) -> dict[str, object]:
    _, entries = _entries(session, profile.id)
    findings = analyse_journal(entries)
    twin = build_twin(profile_id=profile.id, entries=entries, findings=findings)
    return twin.as_dict()


@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
def snapshot(profile: CurrentProfile, session: DbSession) -> dict[str, object]:
    _, entries = _entries(session, profile.id)
    twin = build_twin(profile_id=profile.id, entries=entries)
    row = TwinSnapshot(
        profile_id=profile.id,
        state=twin.as_dict(),
        entry_count=len(entries),
        computed_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return {"id": row.id, "entry_count": row.entry_count}


@router.get("/project")
def projection(scenario: str, profile: CurrentProfile, session: DbSession) -> dict[str, object]:
    """"¿Qué pasa probablemente si...?" (A24).

    Sin base histórica no se proyecta: la respuesta es qué haría falta
    registrar para poder responder.
    """
    try:
        parsed = Scenario(scenario)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_scenario", scenario=scenario) from exc

    _, entries = _entries(session, profile.id)
    findings = analyse_journal(entries)
    twin = build_twin(profile_id=profile.id, entries=entries, findings=findings)
    return project(twin, parsed).as_dict()


@router.get("/scenarios")
def scenarios() -> list[dict[str, str]]:
    return [{"scenario": s.value, "label_key": s.label_key} for s in Scenario]


# --- experimentos ---------------------------------------------------------

experiments_router = APIRouter(prefix="/experiments", tags=["experiments"])


@experiments_router.get("")
def list_experiments(profile: CurrentProfile, session: DbSession) -> list[dict[str, object]]:
    rows = (
        session.execute(select(ExperimentRow).where(ExperimentRow.profile_id == profile.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "question_key": r.question_key,
            "status": r.status,
            "controlled_variables": list(r.controlled_variables or ()),
            "target_repetitions_per_arm": r.target_repetitions_per_arm,
            "shared_anonymously": r.shared_anonymously,
            "arms": [
                {
                    "id": a.id,
                    "label_key": a.label_key,
                    "product_ids": list(a.product_ids or ()),
                    "technique_ids": list(a.technique_ids or ()),
                }
                for a in r.arms
            ],
        }
        for r in rows
    ]


@experiments_router.post("", status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentIn, profile: CurrentProfile, session: DbSession
) -> dict[str, object]:
    active = (
        session.execute(
            select(ExperimentRow).where(
                ExperimentRow.profile_id == profile.id,
                ExperimentRow.status.in_(("draft", "running")),
            )
        )
        .scalars()
        .all()
    )
    if not payload.is_premium and len(active) >= FREE_TIER_ACTIVE_EXPERIMENTS:
        raise Forbidden("error.free_tier_experiment_limit", limit=FREE_TIER_ACTIVE_EXPERIMENTS)

    row = ExperimentRow(
        profile_id=profile.id,
        question_key=payload.question_key,
        status="running",
        controlled_variables=payload.controlled_variables,
        target_repetitions_per_arm=payload.target_repetitions_per_arm,
    )
    session.add(row)
    session.flush()
    for arm in payload.arms:
        session.add(
            ExperimentArmRow(
                experiment_id=row.id,
                label_key=arm.label_key,
                product_ids=arm.product_ids,
                technique_ids=arm.technique_ids,
            )
        )
    session.flush()
    session.refresh(row)
    return {"id": row.id, "arm_ids": [a.id for a in row.arms]}


@experiments_router.get("/{experiment_id}/reading")
def reading(experiment_id: str, profile: CurrentProfile, session: DbSession) -> dict[str, object]:
    """Lectura del experimento con honestidad estadística (A25).

    Puede devolver "todavía no hay suficientes repeticiones", "empate" o
    "inválido porque se rompió una variable controlada". Los tres son
    resultados legítimos.
    """
    row = session.get(ExperimentRow, experiment_id)
    if row is None or row.profile_id != profile.id:
        raise NotFound("experiment", experiment_id=experiment_id)

    experiment = Experiment(
        id=row.id,
        question_key=row.question_key,
        arms=tuple(
            ExperimentArm(
                id=a.id,
                label_key=a.label_key,
                product_ids=tuple(a.product_ids or ()),
                technique_ids=tuple(a.technique_ids or ()),
            )
            for a in row.arms
        ),
        controlled_variables=tuple(row.controlled_variables or ()),
        target_repetitions_per_arm=row.target_repetitions_per_arm,
    )
    _, entries = _entries(session, profile.id)
    return read_experiment(experiment, entries).as_dict()
