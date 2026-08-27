"""Enciclopedia y detector de mitos (A17).

Todo lo educativo lleva su etiqueta de nivel de evidencia visible (B4). Los
mitos aparecen exclusivamente aquí y desmontados: el motor de recomendación no
puede emitirlos porque `UNSUPPORTED_TREND.can_recommend` es False.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...db.session import TransactionalRoute
from ...domain.evidence.levels import EvidenceLevel
from ...domain.rules.engine import detect_myths
from ...domain.rules.model import RuleKind
from ...services.engine import get_rule_engine

router = APIRouter(prefix="/education", tags=["education"], route_class=TransactionalRoute)


@router.get("/myths")
def list_myths() -> list[dict[str, object]]:
    engine = get_rule_engine()
    return [
        {
            "id": rule.id,
            "myth": rule.outcome.get("myth"),
            "message_key": rule.message_key,
            "correction_key": rule.outcome.get("correction_key"),
            "related_concept": rule.outcome.get("related_concept"),
            "mechanism": rule.mechanism,
            "evidence_level": rule.evidence_level.value,
            "evidence_label_key": rule.evidence_level.label_key,
            "tags": list(rule.tags),
        }
        for rule in engine.rules
        if rule.kind is RuleKind.MYTH
    ]


@router.post("/myths/detect")
def detect(statements: list[str]) -> list[dict[str, object]]:
    """Comprueba afirmaciones concretas contra el detector de mitos."""
    engine = get_rule_engine()
    found = detect_myths(engine.rules, statements)
    return [
        {
            "id": rule.id,
            "message_key": rule.message_key,
            "correction_key": rule.outcome.get("correction_key"),
            "mechanism": rule.mechanism,
        }
        for rule in found
    ]


@router.get("/rules")
def list_rules(evidence_level: str | None = None) -> list[dict[str, object]]:
    """Todas las reglas con su procedencia.

    Que esto sea consultable es parte del producto: cualquiera puede auditar en
    qué se basa una recomendación, no solo leer que "se basa en evidencia".
    """
    engine = get_rule_engine()
    wanted = EvidenceLevel(evidence_level) if evidence_level else None
    return [
        {
            "id": rule.id,
            "kind": rule.kind.value,
            "evidence_level": rule.evidence_level.value,
            "evidence_label_key": rule.evidence_level.label_key,
            "evidence_confidence": rule.evidence_level.confidence,
            "mechanism": rule.mechanism,
            "sources": list(rule.sources),
            "message_key": rule.message_key,
            "tags": list(rule.tags),
        }
        for rule in engine.rules
        if wanted is None or rule.evidence_level is wanted
    ]


@router.get("/evidence-levels")
def evidence_levels() -> list[dict[str, object]]:
    return [
        {
            "level": level.value,
            "label_key": level.label_key,
            "confidence": level.confidence,
            "can_recommend": level.can_recommend,
        }
        for level in EvidenceLevel
    ]
