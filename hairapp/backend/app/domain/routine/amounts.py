"""Cantidades inteligentes (A10).

La cantidad de producto escala con la **superficie total de fibra**, no con la
longitud. Superficie ≈ (nº de hebras) × (perímetro de hebra) × longitud, así que
densidad y diámetro pesan tanto como el largo. Es la razón por la que "una
moneda de dos euros" funciona para una persona y apelmaza a otra.

La salida siempre incluye una referencia visual concreta además de los ml: casi
nadie tiene una balanza en la ducha.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ..hair.attributes import Density, StrandDiameter
from ..hair.zones import Zone, ZoneGroup, group_of


class ProductCategory(enum.Enum):
    SHAMPOO = "shampoo"
    CO_WASH = "co_wash"
    CONDITIONER = "conditioner"
    DEEP_CONDITIONER = "deep_conditioner"
    LEAVE_IN = "leave_in"
    CREAM = "cream"
    GEL = "gel"
    MOUSSE = "mousse"
    OIL = "oil"
    SERUM = "serum"
    CLARIFYING_SHAMPOO = "clarifying_shampoo"
    PROTEIN_TREATMENT = "protein_treatment"
    SCALP_PRODUCT = "scalp_product"
    HEAT_PROTECTANT = "heat_protectant"


#: ml por cada 10 cm de longitud, para densidad media y diámetro medio,
#: aplicado a la cabeza entera. Los factores de zona reparten esta base.
_BASE_ML_PER_10CM: dict[ProductCategory, float] = {
    ProductCategory.SHAMPOO: 3.0,
    ProductCategory.CO_WASH: 5.0,
    ProductCategory.CONDITIONER: 5.0,
    ProductCategory.DEEP_CONDITIONER: 7.0,
    ProductCategory.LEAVE_IN: 2.5,
    ProductCategory.CREAM: 3.0,
    ProductCategory.GEL: 3.5,
    ProductCategory.MOUSSE: 4.0,
    ProductCategory.OIL: 0.8,
    ProductCategory.SERUM: 0.6,
    ProductCategory.CLARIFYING_SHAMPOO: 3.0,
    ProductCategory.PROTEIN_TREATMENT: 4.0,
    ProductCategory.SCALP_PRODUCT: 1.5,
    ProductCategory.HEAT_PROTECTANT: 2.0,
}

_DENSITY_FACTOR: dict[Density, float] = {
    Density.LOW: 0.7,
    Density.MEDIUM: 1.0,
    Density.HIGH: 1.35,
}

_DIAMETER_FACTOR: dict[StrandDiameter, float] = {
    StrandDiameter.FINE: 0.8,
    StrandDiameter.MEDIUM: 1.0,
    StrandDiameter.COARSE: 1.2,
}

#: Fracción de la cantidad total que corresponde a cada grupo de zonas.
_ZONE_GROUP_SHARE: dict[ZoneGroup, float] = {
    ZoneGroup.FRONT: 0.18,
    ZoneGroup.SIDES: 0.30,
    ZoneGroup.TOP: 0.20,
    ZoneGroup.BACK: 0.22,
    ZoneGroup.ENDS: 0.10,
}

#: Productos que van solo al cuero cabelludo: no se reparten por largo.
_SCALP_ONLY = {ProductCategory.SHAMPOO, ProductCategory.CLARIFYING_SHAMPOO, ProductCategory.SCALP_PRODUCT}


@dataclass(frozen=True)
class VisualReference:
    """Referencia visual concreta para una cantidad."""

    key: str
    approx_ml: float


#: Referencias ordenadas de menor a mayor. Los ml son aproximaciones de uso
#: común; sirven para elegir la referencia más cercana, no como medida exacta.
_REFERENCES: tuple[VisualReference, ...] = (
    VisualReference("amount.ref.few_drops", 0.3),
    VisualReference("amount.ref.pea", 0.6),
    VisualReference("amount.ref.chickpea", 1.2),
    VisualReference("amount.ref.almond", 2.0),
    VisualReference("amount.ref.coin", 3.0),
    VisualReference("amount.ref.teaspoon", 5.0),
    VisualReference("amount.ref.walnut", 8.0),
    VisualReference("amount.ref.tablespoon", 15.0),
    VisualReference("amount.ref.golf_ball", 25.0),
    VisualReference("amount.ref.palmful", 40.0),
)


@dataclass(frozen=True)
class Amount:
    ml: float
    reference: VisualReference
    reference_multiplier: float
    zone: Zone | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "ml": round(self.ml, 2),
            "reference_key": self.reference.key,
            "reference_multiplier": round(self.reference_multiplier, 1),
            "zone": self.zone.value if self.zone else None,
        }


def closest_reference(ml: float) -> tuple[VisualReference, float]:
    """Elige la referencia visual más cercana y cuántas veces la repite.

    Prefiere un múltiplo pequeño de una referencia grande antes que un múltiplo
    grande de una pequeña: "dos cucharaditas" se entiende, "ocho guisantes" no.
    """
    best: tuple[VisualReference, float] | None = None
    best_error = float("inf")
    for reference in _REFERENCES:
        multiplier = ml / reference.approx_ml
        if multiplier < 0.5 or multiplier > 4.0:
            continue
        rounded = round(multiplier * 2) / 2
        if rounded <= 0:
            continue
        # Además del error de aproximación, se penaliza lo que hace difícil
        # de seguir una instrucción: múltiplos altos («ocho guisantes»),
        # fracciones de una referencia («media almendra») y medios
        # («dos cucharaditas y media»).
        error = abs(rounded * reference.approx_ml - ml)
        error += rounded * 0.15
        if rounded < 1:
            error += 0.5
        if rounded % 1:
            error += 0.3
        if error < best_error:
            best_error = error
            best = (reference, rounded)
    if best is None:
        # Fuera de todos los rangos: se usa la referencia extrema más cercana.
        reference = _REFERENCES[0] if ml < _REFERENCES[0].approx_ml else _REFERENCES[-1]
        return reference, max(0.5, round(ml / reference.approx_ml * 2) / 2)
    return best


def compute_amount(
    category: ProductCategory,
    *,
    length_cm: float,
    density: Density,
    strand_diameter: StrandDiameter,
    zone: Zone | None = None,
    modifier: float = 1.0,
) -> Amount:
    """Cantidad para una categoría, opcionalmente acotada a una zona.

    `modifier` viene de las reglas (por ejemplo `style.less_product_fine`
    aplica 0.6). Se aplica al final para que la trazabilidad sea clara.
    """
    base = _BASE_ML_PER_10CM[category]
    length_factor = max(0.4, length_cm / 10.0)

    if category in _SCALP_ONLY:
        # El champú no escala con el largo: el cuero cabelludo mide lo mismo.
        length_factor = 1.6

    ml = base * length_factor * _DENSITY_FACTOR[density] * _DIAMETER_FACTOR[strand_diameter] * modifier

    if zone is not None:
        if category in _SCALP_ONLY and zone is Zone.ENDS:
            ml = 0.0
        else:
            group = group_of(zone)
            zones_in_group = _group_size(group)
            ml *= _ZONE_GROUP_SHARE[group] / zones_in_group

    reference, multiplier = closest_reference(max(ml, 0.05))
    return Amount(ml=ml, reference=reference, reference_multiplier=multiplier, zone=zone)


def _group_size(group: ZoneGroup) -> int:
    from ..hair.zones import ZONE_GROUPS

    return len(ZONE_GROUPS[group])
