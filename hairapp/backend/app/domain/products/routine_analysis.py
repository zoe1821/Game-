"""Análisis de compatibilidad de una rutina completa (A11).

Analizar productos de uno en uno no detecta lo que de verdad falla: tres
productos que hacen lo mismo, proteína repetida en cuatro capas, o siliconas no
solubles sin nada que las retire. Este módulo mira la rutina como conjunto.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..common import Explanation
from ..routine.amounts import ProductCategory
from .catalog import Level, Product, SurfactantStrength
from .ingredients import Function, function_profile


class Severity(enum.Enum):
    INFO = "info"
    ATTENTION = "attention"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class RoutineFinding:
    key: str
    severity: Severity
    product_ids: tuple[str, ...]
    params: dict[str, object] = field(default_factory=dict)
    suggestion_key: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "severity": self.severity.value,
            "product_ids": list(self.product_ids),
            "params": dict(self.params),
            "suggestion_key": self.suggestion_key,
        }


@dataclass(frozen=True)
class RoutineAnalysis:
    findings: tuple[RoutineFinding, ...]
    explanation: Explanation

    @property
    def conflicts(self) -> tuple[RoutineFinding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.CONFLICT)

    def as_dict(self) -> dict[str, object]:
        return {
            "findings": [f.as_dict() for f in self.findings],
            "explanation": self.explanation.as_dict(),
        }


#: Categorías que se quedan en el cabello. La acumulación solo importa aquí:
#: lo que se enjuaga no se acumula igual.
_LEAVE_ON = {
    ProductCategory.LEAVE_IN,
    ProductCategory.CREAM,
    ProductCategory.GEL,
    ProductCategory.MOUSSE,
    ProductCategory.OIL,
    ProductCategory.SERUM,
    ProductCategory.HEAT_PROTECTANT,
}

_CLEANSERS = {ProductCategory.SHAMPOO, ProductCategory.CLARIFYING_SHAMPOO}

#: Categorías que cumplen un papel intercambiable: tener las tres a la vez suele
#: ser gasto repetido, no una rutina mejor.
_REDUNDANT_GROUPS: tuple[tuple[ProductCategory, ...], ...] = (
    (ProductCategory.CREAM, ProductCategory.LEAVE_IN),
    (ProductCategory.GEL, ProductCategory.MOUSSE),
    (ProductCategory.OIL, ProductCategory.SERUM),
)

_LEVEL_SCORE = {Level.NONE: 0, Level.LOW: 1, Level.MEDIUM: 2, Level.HIGH: 3}


def analyse_routine(
    products: Sequence[Product],
    *,
    porosity: str | None = None,
    washes_per_week: float = 2.0,
) -> RoutineAnalysis:
    findings: list[RoutineFinding] = []

    findings += _protein_load(products)
    findings += _buildup_risk(products)
    findings += _redundancy(products)
    findings += _humectant_stacking(products, porosity)
    findings += _cleansing_gap(products, washes_per_week)

    explanation = Explanation(
        summary_key="routine_analysis.summary",
        inputs_used=("input.routine_products", "input.hair_profile"),
        observations=tuple(f.key for f in findings),
        evidence_level="professional_consensus",
        evidence_confidence=0.70,
        personal_confidence=0.0,
        sample_size=0,
        uncertainty_keys=("uncertainty.formulation_details_unknown",),
        params={"product_count": len(products)},
    )
    return RoutineAnalysis(findings=tuple(findings), explanation=explanation)


def _protein_load(products: Sequence[Product]) -> list[RoutineFinding]:
    """Proteína repetida en varias capas.

    El problema no es la proteína: es acumularla sin emolientes que compensen.
    Por eso la severidad depende de la relación proteína/emoliente, no de la
    proteína sola.
    """
    carrying = [p for p in products if _LEVEL_SCORE[p.protein_level] >= 2]
    if len(carrying) < 2:
        return []

    protein_score = sum(_LEVEL_SCORE[p.protein_level] for p in carrying)
    emollient_score = sum(_LEVEL_SCORE[p.emollient_level] for p in products)

    severity = Severity.ATTENTION
    if protein_score >= 6 and emollient_score < protein_score:
        severity = Severity.CONFLICT

    return [
        RoutineFinding(
            key="routine.protein_stacked_across_layers",
            severity=severity,
            product_ids=tuple(p.id for p in carrying),
            params={
                "layers_with_protein": len(carrying),
                "protein_score": protein_score,
                "emollient_score": emollient_score,
            },
            suggestion_key="routine.suggestion.space_protein_or_add_emollients",
        )
    ]


def _buildup_risk(products: Sequence[Product]) -> list[RoutineFinding]:
    """Siliconas no solubles sin un tensioactivo capaz de retirarlas.

    Esta es la versión correcta del mito "silicona = malo": el problema no es
    la molécula, es la incoherencia entre lo que se deja y lo que limpia.
    """
    with_insoluble = [
        p
        for p in products
        if p.category in _LEAVE_ON
        and function_profile(p.ingredients).has(Function.SILICONE_INSOLUBLE, threshold=0.03)
    ]
    if not with_insoluble:
        return []

    strong_enough = [
        p
        for p in products
        if p.category in _CLEANSERS
        and p.surfactant_strength in {SurfactantStrength.MEDIUM, SurfactantStrength.STRONG}
    ]
    if strong_enough:
        return [
            RoutineFinding(
                key="routine.insoluble_silicone_covered_by_cleanser",
                severity=Severity.INFO,
                product_ids=tuple(p.id for p in with_insoluble),
                params={"cleanser_ids": [p.id for p in strong_enough]},
            )
        ]

    return [
        RoutineFinding(
            key="routine.insoluble_silicone_without_capable_cleanser",
            severity=Severity.CONFLICT,
            product_ids=tuple(p.id for p in with_insoluble),
            suggestion_key="routine.suggestion.add_capable_cleanser_or_swap_silicone",
        )
    ]


def _redundancy(products: Sequence[Product]) -> list[RoutineFinding]:
    """Productos que hacen lo mismo. Es dinero repetido, no mejor resultado."""
    findings: list[RoutineFinding] = []
    by_category: dict[ProductCategory, list[Product]] = {}
    for product in products:
        by_category.setdefault(product.category, []).append(product)

    for category, group in by_category.items():
        if len(group) > 1 and category in _LEAVE_ON:
            findings.append(
                RoutineFinding(
                    key="routine.duplicate_category",
                    severity=Severity.INFO,
                    product_ids=tuple(p.id for p in group),
                    params={"category": category.value, "count": len(group)},
                    suggestion_key="routine.suggestion.use_one_at_a_time",
                )
            )

    for overlapping in _REDUNDANT_GROUPS:
        present = [p for p in products if p.category in overlapping]
        categories = {p.category for p in present}
        if len(categories) == len(overlapping) and len(present) >= len(overlapping):
            findings.append(
                RoutineFinding(
                    key="routine.overlapping_roles",
                    severity=Severity.INFO,
                    product_ids=tuple(p.id for p in present),
                    params={"categories": [c.value for c in overlapping]},
                    suggestion_key="routine.suggestion.test_removing_one",
                )
            )
    return findings


def _humectant_stacking(products: Sequence[Product], porosity: str | None) -> list[RoutineFinding]:
    high = [p for p in products if p.category in _LEAVE_ON and p.humectant_level is Level.HIGH]
    if len(high) < 2:
        return []
    return [
        RoutineFinding(
            key="routine.humectants_stacked",
            severity=Severity.ATTENTION,
            product_ids=tuple(p.id for p in high),
            params={"porosity": porosity, "layers": len(high)},
            suggestion_key="routine.suggestion.humectants_depend_on_dew_point",
        )
    ]


def _cleansing_gap(products: Sequence[Product], washes_per_week: float) -> list[RoutineFinding]:
    leave_on = [p for p in products if p.category in _LEAVE_ON]
    cleansers = [p for p in products if p.category in _CLEANSERS or p.category is ProductCategory.CO_WASH]
    if leave_on and not cleansers:
        return [
            RoutineFinding(
                key="routine.no_cleanser_declared",
                severity=Severity.ATTENTION,
                product_ids=(),
                params={"leave_on_count": len(leave_on)},
                suggestion_key="routine.suggestion.declare_your_cleanser",
            )
        ]
    return []
