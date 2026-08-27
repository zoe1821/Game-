"""Inventario personal y emparejamiento de productos.

El orden de este módulo refleja la filosofía anti-consumista (A15): primero se
mira lo que ya se tiene, y solo si no cubre la necesidad se habla de comprar.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, status
from sqlalchemy import select

from ...core.errors import NotFound, ValidationFailed
from ...domain.products.catalog import InventoryItem, Product
from ...domain.products.ingredients import analyse, parse_inci, summarise_functions
from ...domain.products.matching import compare, match_for_step
from ...domain.products.routine_analysis import analyse_routine
from ...domain.routine.amounts import ProductCategory
from ...models.products import InventoryRow, ProductRow, SensitivityRow
from ...schemas.journal import IngredientScanIn, InventoryItemIn, MatchRequestIn
from ..deps import CurrentProfile, DbSession

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _to_domain_product(row: ProductRow) -> Product:
    return Product.from_inci(
        inci=row.inci_raw or "",
        id=row.id,
        brand=row.brand,
        name=row.name,
        category=ProductCategory(row.category),
        size_ml=row.size_ml,
        price_minor_units=row.price_minor_units,
        currency=row.currency,
        available_in=tuple(row.available_in or ()),
    )


def _to_domain_item(row: InventoryRow) -> InventoryItem:
    return InventoryItem(
        id=row.id,
        product=_to_domain_product(row.product) if row.product else None,
        custom_name=row.custom_name,
        custom_category=ProductCategory(row.custom_category) if row.custom_category else None,
        custom_inci=row.custom_inci,
        amount_left_ratio=row.amount_left_ratio,
        opened_at=row.opened_at.isoformat() if row.opened_at else None,
        pao_months=row.pao_months,
        disliked=row.disliked,
        notes=row.notes,
    )


def _load_inventory(session: DbSession, profile_id: str) -> list[InventoryRow]:
    return list(
        session.execute(select(InventoryRow).where(InventoryRow.profile_id == profile_id))
        .scalars()
        .all()
    )


@router.get("")
def list_inventory(profile: CurrentProfile, session: DbSession) -> list[dict[str, object]]:
    rows = _load_inventory(session, profile.id)
    today = date.today()
    out = []
    for row in rows:
        item = _to_domain_item(row)
        expires = row.expires_on
        out.append(
            {
                "id": row.id,
                "display_name": item.display_name,
                "category": item.category.value if item.category else None,
                "amount_left_ratio": row.amount_left_ratio,
                "disliked": row.disliked,
                "is_usable": item.is_usable,
                "opened_at": row.opened_at.isoformat() if row.opened_at else None,
                "pao_months": row.pao_months,
                "expires_on": expires.isoformat() if expires else None,
                "expired": bool(expires and expires < today),
                "notes": row.notes,
            }
        )
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
def add_item(
    payload: InventoryItemIn, profile: CurrentProfile, session: DbSession
) -> dict[str, object]:
    if payload.product_id is None and not (payload.custom_name and payload.custom_category):
        raise ValidationFailed("error.inventory_needs_product_or_name")
    if payload.custom_category is not None:
        try:
            ProductCategory(payload.custom_category)
        except ValueError as exc:
            raise ValidationFailed(
                "error.unknown_category", category=payload.custom_category
            ) from exc

    row = InventoryRow(
        profile_id=profile.id,
        product_id=payload.product_id,
        custom_name=payload.custom_name,
        custom_category=payload.custom_category,
        custom_inci=payload.custom_inci,
        opened_at=payload.opened_at,
        pao_months=payload.pao_months,
        notes=payload.notes,
    )
    session.add(row)
    session.flush()
    return {"id": row.id}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(item_id: str, profile: CurrentProfile, session: DbSession) -> None:
    row = session.get(InventoryRow, item_id)
    if row is None or row.profile_id != profile.id:
        raise NotFound("inventory_item", item_id=item_id)
    session.delete(row)


@router.get("/duplicates")
def find_duplicates(profile: CurrentProfile, session: DbSession) -> list[dict[str, object]]:
    """Detección de duplicados para la wishlist (A15).

    El objetivo explícito es que la respuesta más frecuente a "¿qué compro?"
    sea "nada, ya tienes uno".
    """
    rows = _load_inventory(session, profile.id)
    by_category: dict[str, list[InventoryRow]] = {}
    for row in rows:
        item = _to_domain_item(row)
        if item.category is None or not item.is_usable:
            continue
        by_category.setdefault(item.category.value, []).append(row)

    return [
        {
            "category": category,
            "count": len(group),
            "item_ids": [r.id for r in group],
            "message_key": "inventory.duplicate_category",
        }
        for category, group in by_category.items()
        if len(group) > 1
    ]


@router.post("/match")
def match(
    payload: MatchRequestIn, profile: CurrentProfile, session: DbSession
) -> dict[str, object]:
    """Qué usar para un paso concreto. Empieza siempre por el inventario."""
    try:
        parsed = ProductCategory(payload.category)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_category", category=payload.category) from exc

    inventory = [_to_domain_item(r) for r in _load_inventory(session, profile.id)]
    catalog_rows = (
        session.execute(
            select(ProductRow).where(ProductRow.category == payload.category).limit(200)
        )
        .scalars()
        .all()
    )
    catalog = [_to_domain_product(r) for r in catalog_rows]

    result = match_for_step(
        category=parsed,
        wanted_attributes=payload.wanted_attributes,
        inventory=inventory,
        catalog=catalog,
    )
    return result.as_dict()


@router.post("/analyse-routine")
def analyse_current_routine(
    profile: CurrentProfile, session: DbSession, product_ids: list[str] | None = None
) -> dict[str, object]:
    """Análisis de compatibilidad de la rutina completa (A11)."""
    if product_ids:
        rows = (
            session.execute(select(ProductRow).where(ProductRow.id.in_(product_ids)))
            .scalars()
            .all()
        )
        products = [_to_domain_product(r) for r in rows]
    else:
        products = [
            product
            for item in (_to_domain_item(r) for r in _load_inventory(session, profile.id))
            if item.is_usable and (product := item.as_product()) is not None
        ]

    porosities = [
        payload["value"]
        for zone in profile.zones
        for field, payload in zone.measurements.items()
        if field == "porosity"
    ]
    dominant = max(set(porosities), key=porosities.count) if porosities else None
    return analyse_routine(products, porosity=dominant).as_dict()


@router.post("/scan-ingredients", tags=["ingredients"])
def scan_ingredients(
    payload: IngredientScanIn,
    profile: CurrentProfile,
    session: DbSession,
) -> dict[str, object]:
    """Ingredient scanner (A11).

    Analiza por función y formulación, no con reglas de "bueno/malo". También
    avisa de coincidencias con las sensibilidades **declaradas** por la
    persona, sin valorarlas ni diagnosticar nada.
    """
    ingredients = parse_inci(payload.inci)
    if not ingredients:
        raise ValidationFailed("error.empty_inci")

    porosities = [
        payload["value"]
        for zone in profile.zones
        for field, payload in zone.measurements.items()
        if field == "porosity"
    ]
    dominant = max(set(porosities), key=porosities.count) if porosities else None

    declared = (
        session.execute(
            select(SensitivityRow.inci_name).where(SensitivityRow.profile_id == profile.id)
        )
        .scalars()
        .all()
    )
    lowered = {d.strip().lower() for d in declared}
    matches = [i.inci_name for i in ingredients if i.inci_name.lower() in lowered]

    findings = analyse(ingredients, porosity=dominant)
    return {
        "ingredients": [
            {"inci_name": i.inci_name, "functions": [f.value for f in i.functions]}
            for i in ingredients
        ],
        "by_function": summarise_functions(ingredients),
        "findings": [
            {
                "key": f.key,
                "severity": f.severity,
                "function": f.function.value if f.function else None,
                "params": f.params,
            }
            for f in findings
        ],
        "declared_sensitivity_matches": matches,
        "unrecognised_count": sum(
            1 for i in ingredients if [f.value for f in i.functions] == ["other"]
        ),
    }


@router.post("/compare")
def compare_products(product_ids: list[str], session: DbSession) -> list[dict[str, object]]:
    """Comparador de hasta 4 productos (A11)."""
    if len(product_ids) > 4:
        raise ValidationFailed("error.too_many_products_to_compare", limit=4)
    rows = session.execute(select(ProductRow).where(ProductRow.id.in_(product_ids))).scalars().all()
    products = [_to_domain_product(r) for r in rows]
    return [
        {"attribute": row.attribute, "values": list(row.values), "differs": row.differs}
        for row in compare(products)
    ]
