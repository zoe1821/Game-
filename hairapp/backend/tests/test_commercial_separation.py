"""Invariante de negocio verificado por código (docs/02-MONETIZATION.md §4).

El motor de recomendación de productos no puede estar acoplado al modelo de
ingresos. No basta con la intención: si el módulo *puede* leer datos
comerciales, algún día los leerá. Estos tests fallan si alguien los introduce.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.domain.products import catalog, matching
from app.domain.products.catalog import Product
from app.domain.routine.amounts import ProductCategory

#: Nombres que representan una relación comercial. Ninguno puede aparecer en el
#: modelo de producto ni en el motor de emparejamiento.
COMMERCIAL_NAMES = {
    "sponsored",
    "is_sponsored",
    "partner_id",
    "partner",
    "commission",
    "commission_rate",
    "affiliate",
    "affiliate_url",
    "affiliate_link",
    "paid_placement",
    "promoted",
    "ad_id",
    "advertiser",
    "revenue_share",
    "boost",
}


def test_product_model_has_no_commercial_fields() -> None:
    fields = set(Product.__dataclass_fields__)
    assert not (fields & COMMERCIAL_NAMES), (
        "El modelo Product no puede llevar campos comerciales: "
        f"{sorted(fields & COMMERCIAL_NAMES)}"
    )


def test_matching_module_never_mentions_commercial_concepts() -> None:
    source = Path(inspect.getfile(matching)).read_text(encoding="utf-8")
    tree = ast.parse(source)

    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr.lower())
        elif isinstance(node, ast.arg) or isinstance(node, ast.keyword) and node.arg:
            identifiers.add(node.arg.lower())

    offending = identifiers & COMMERCIAL_NAMES
    assert not offending, f"el motor de matching toca conceptos comerciales: {sorted(offending)}"


def test_matching_imports_nothing_outside_the_domain() -> None:
    """Si el matcher pudiera importar servicios o modelos de DB, podría llegar
    a una tabla comercial por la puerta de atrás."""
    source = Path(inspect.getfile(matching)).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_roots = {"app.models", "app.services", "app.api", "sqlalchemy", "requests", "httpx"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(r) for r in forbidden_roots), alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # Los imports relativos se quedan dentro del dominio por construcción.
            if node.level == 0:
                assert not any(module.startswith(r) for r in forbidden_roots), module


def test_catalog_module_has_no_commercial_fields_anywhere() -> None:
    source = Path(inspect.getfile(catalog)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assert node.target.id.lower() not in COMMERCIAL_NAMES, node.target.id


def test_ranking_depends_only_on_attribute_fit() -> None:
    """Dos productos idénticos en atributos deben empatar, sea cual sea la marca."""
    from app.domain.products.matching import check_attributes

    wanted = {"hold_level": ["medium", "strong"], "film_forming": True}
    inci = "Aqua, VP/VA Copolymer, PVP, Glycerin, Phenoxyethanol"
    a = Product.from_inci(inci=inci, id="a", brand="MarcaGrande", name="Gel", category=ProductCategory.GEL)
    b = Product.from_inci(inci=inci, id="b", brand="marca-pequeña", name="Gel", category=ProductCategory.GEL)

    checks_a = [c.status for c in check_attributes(a, wanted)]
    checks_b = [c.status for c in check_attributes(b, wanted)]
    assert checks_a == checks_b
