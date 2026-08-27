"""Emparejamiento de productos — explicable y con el inventario primero.

Dos reglas de producto que este módulo implementa literalmente:

1. **A15 / B1**: la primera respuesta a "¿qué uso?" es lo que la persona ya
   tiene. Una recomendación de compra solo aparece si el inventario no cubre la
   necesidad, y se dice explícitamente por qué no la cubre.
2. **B1 §4**: este módulo **no importa nada comercial**. Recibe perfil, zonas,
   objetivos, inventario, clima e historial. Nada más. La ausencia de entradas
   comerciales está verificada por `tests/test_commercial_separation.py`.

Tampoco produce falsa precisión: no hay "97% de compatibilidad". Hay atributos
que coinciden, atributos que no, y lo que no se pudo comprobar.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..common import Explanation
from ..confidence.engine import ConfidenceReport
from ..routine.amounts import ProductCategory
from .catalog import InventoryItem, Product


class MatchOutcome(enum.Enum):
    ALREADY_OWNED = "already_owned"
    """Ya lo tienes y sirve. Es el mejor resultado posible."""
    OWNED_PARTIAL = "owned_partial"
    """Ya tienes algo que sirve a medias; se dice en qué se queda corto."""
    NEEDS_PRODUCT = "needs_product"
    """El inventario no cubre esto. Solo aquí se sugiere algo nuevo."""
    UNVERIFIABLE = "unverifiable"
    """No hay datos suficientes para decidir. Se dice, no se rellena."""


@dataclass(frozen=True)
class AttributeCheck:
    """El resultado de comprobar un atributo pedido contra un producto."""

    attribute: str
    wanted: Any
    actual: Any
    status: str  # "match" | "mismatch" | "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "attribute": self.attribute,
            "wanted": _plain(self.wanted),
            "actual": _plain(self.actual),
            "status": self.status,
        }


@dataclass(frozen=True)
class ProductMatch:
    """Un candidato con su desglose. Sin puntuación única engañosa."""

    product: Product
    checks: tuple[AttributeCheck, ...]
    from_inventory: bool
    inventory_item_id: str | None = None

    @property
    def matched(self) -> tuple[AttributeCheck, ...]:
        return tuple(c for c in self.checks if c.status == "match")

    @property
    def mismatched(self) -> tuple[AttributeCheck, ...]:
        return tuple(c for c in self.checks if c.status == "mismatch")

    @property
    def unknown(self) -> tuple[AttributeCheck, ...]:
        return tuple(c for c in self.checks if c.status == "unknown")

    @property
    def is_full_match(self) -> bool:
        return not self.mismatched and bool(self.matched)

    def as_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product.id,
            "brand": self.product.brand,
            "name": self.product.name,
            "category": self.product.category.value,
            "from_inventory": self.from_inventory,
            "inventory_item_id": self.inventory_item_id,
            "matched": [c.as_dict() for c in self.matched],
            "mismatched": [c.as_dict() for c in self.mismatched],
            "unknown": [c.as_dict() for c in self.unknown],
        }


@dataclass(frozen=True)
class MatchResult:
    outcome: MatchOutcome
    category: ProductCategory
    from_inventory: tuple[ProductMatch, ...]
    suggestions: tuple[ProductMatch, ...]
    explanation: Explanation
    unmet_attributes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "category": self.category.value,
            "from_inventory": [m.as_dict() for m in self.from_inventory],
            "suggestions": [m.as_dict() for m in self.suggestions],
            "unmet_attributes": list(self.unmet_attributes),
            "explanation": self.explanation.as_dict(),
        }


def check_attributes(product: Product, wanted: Mapping[str, Any]) -> tuple[AttributeCheck, ...]:
    """Comprueba cada atributo pedido. Lo desconocido se marca desconocido."""
    checks: list[AttributeCheck] = []
    for attribute, want in wanted.items():
        actual = product.attribute(attribute)
        if actual is None:
            checks.append(AttributeCheck(attribute, want, None, "unknown"))
            continue
        checks.append(
            AttributeCheck(
                attribute,
                want,
                actual,
                "match" if _satisfies(actual, want) else "mismatch",
            )
        )
    return tuple(checks)


def _satisfies(actual: Any, want: Any) -> bool:
    actual_value = _plain(actual)
    if isinstance(want, (list, tuple, set)):
        return actual_value in {_plain(w) for w in want}
    return actual_value == _plain(want)


def _plain(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    return value


def match_for_step(
    *,
    category: ProductCategory,
    wanted_attributes: Mapping[str, Any],
    inventory: Sequence[InventoryItem],
    catalog: Sequence[Product] = (),
    confidence: ConfidenceReport | None = None,
    max_suggestions: int = 3,
) -> MatchResult:
    """Resuelve qué usar para un paso de la rutina.

    El orden es siempre el mismo y no es configurable: inventario, inventario
    parcial, y solo entonces catálogo.
    """
    wanted = {k: v for k, v in wanted_attributes.items() if k != "frequency_hint"}

    owned_matches: list[ProductMatch] = []
    for item in inventory:
        if not item.is_usable or item.category is not category:
            continue
        product = item.as_product()
        if product is None:
            # Está en el inventario pero no sabemos qué lleva: no se descarta ni
            # se aprueba, se declara no verificable.
            continue
        owned_matches.append(
            ProductMatch(
                product=product,
                checks=check_attributes(product, wanted),
                from_inventory=True,
                inventory_item_id=item.id,
            )
        )

    owned_matches.sort(key=_rank_match, reverse=True)

    full = [m for m in owned_matches if m.is_full_match]
    if full:
        return MatchResult(
            outcome=MatchOutcome.ALREADY_OWNED,
            category=category,
            from_inventory=tuple(full),
            suggestions=(),
            explanation=_explain(
                "match.already_owned",
                full[0],
                confidence,
                extra_inputs=("input.inventory",),
            ),
        )

    unmet: tuple[str, ...] = ()
    if owned_matches:
        best = owned_matches[0]
        unmet = tuple(c.attribute for c in best.mismatched)
        # Aunque haya algo parcial, se ofrecen alternativas del catálogo: la
        # decisión de comprar o no es de la persona, con la carencia a la vista.
        suggestions = _catalog_suggestions(category, wanted, catalog, max_suggestions)
        return MatchResult(
            outcome=MatchOutcome.OWNED_PARTIAL,
            category=category,
            from_inventory=tuple(owned_matches[:max_suggestions]),
            suggestions=tuple(suggestions),
            explanation=_explain(
                "match.owned_partial",
                best,
                confidence,
                extra_inputs=("input.inventory",),
                params={"unmet_attributes": list(unmet)},
            ),
            unmet_attributes=unmet,
        )

    suggestions = _catalog_suggestions(category, wanted, catalog, max_suggestions)
    if not suggestions:
        return MatchResult(
            outcome=MatchOutcome.UNVERIFIABLE,
            category=category,
            from_inventory=(),
            suggestions=(),
            explanation=Explanation(
                summary_key="match.no_data",
                inputs_used=("input.inventory", "input.catalog"),
                evidence_level="professional_consensus",
                evidence_confidence=0.0,
                personal_confidence=0.0,
                sample_size=0,
                uncertainty_keys=("uncertainty.no_catalog_coverage",),
            ),
        )

    return MatchResult(
        outcome=MatchOutcome.NEEDS_PRODUCT,
        category=category,
        from_inventory=(),
        suggestions=tuple(suggestions),
        explanation=_explain(
            "match.needs_product",
            suggestions[0],
            confidence,
            extra_inputs=("input.inventory", "input.catalog"),
        ),
    )


def _catalog_suggestions(
    category: ProductCategory,
    wanted: Mapping[str, Any],
    catalog: Sequence[Product],
    limit: int,
) -> list[ProductMatch]:
    candidates = [
        ProductMatch(
            product=product,
            checks=check_attributes(product, wanted),
            from_inventory=False,
        )
        for product in catalog
        if product.category is category
    ]
    candidates.sort(key=_rank_match, reverse=True)
    return candidates[:limit]


def _rank_match(match: ProductMatch) -> tuple[int, int, int]:
    """Orden: más aciertos, menos fallos, menos incógnitas.

    Deliberadamente **no** es una puntuación de 0 a 100. Una cifra así
    aparentaría una precisión que estos datos no tienen.
    """
    return (len(match.matched), -len(match.mismatched), -len(match.unknown))


def _explain(
    summary_key: str,
    match: ProductMatch,
    confidence: ConfidenceReport | None,
    *,
    extra_inputs: tuple[str, ...] = (),
    params: dict[str, Any] | None = None,
) -> Explanation:
    base_params: dict[str, Any] = {
        "product_id": match.product.id,
        "matched_attributes": [c.attribute for c in match.matched],
        "mismatched_attributes": [c.attribute for c in match.mismatched],
        "unknown_attributes": [c.attribute for c in match.unknown],
    }
    base_params.update(params or {})

    uncertainty = list(confidence.uncertainty_keys) if confidence else []
    if match.unknown:
        uncertainty.append("uncertainty.unverified_product_attributes")

    return Explanation(
        summary_key=summary_key,
        inputs_used=("input.hair_profile", "input.goals", *extra_inputs),
        observations=tuple(c.attribute for c in match.matched),
        evidence_level=confidence.evidence_level.value if confidence else "professional_consensus",
        evidence_confidence=confidence.evidence_confidence if confidence else 0.70,
        personal_confidence=confidence.personal_confidence if confidence else 0.0,
        sample_size=confidence.sample_size if confidence else 0,
        uncertainty_keys=tuple(dict.fromkeys(uncertainty)),
        alternatives=tuple(c.attribute for c in match.mismatched),
        params=base_params,
    )


@dataclass(frozen=True)
class ComparisonRow:
    attribute: str
    values: tuple[Any, ...]
    differs: bool


def compare(products: Sequence[Product], attributes: Sequence[str] | None = None) -> list[ComparisonRow]:
    """Comparador de hasta 4 productos (A11).

    Marca qué filas difieren de verdad, para que la comparación no sea una
    tabla de treinta filas idénticas donde no se ve lo que importa.
    """
    if len(products) > 4:
        raise ValueError("la comparación admite un máximo de 4 productos")
    fields = attributes or (
        "category",
        "hold_level",
        "weight",
        "protein_level",
        "humectant_level",
        "emollient_level",
        "surfactant_strength",
        "cationic",
        "film_forming",
        "chelating",
        "uv_filter",
        "price_per_ml",
    )
    rows: list[ComparisonRow] = []
    for attribute in fields:
        values = tuple(_plain(p.attribute(attribute)) for p in products)
        rows.append(ComparisonRow(attribute, values, len(set(map(str, values))) > 1))
    return rows
