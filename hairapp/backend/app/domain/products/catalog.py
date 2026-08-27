"""Modelo de producto del catálogo.

**Invariante de arquitectura (B1 §4):** este módulo no tiene, y no puede tener,
campos comerciales. No existen `sponsored`, `partner_id`, `commission_rate` ni
`affiliate_url`. Si en el futuro hubiera una relación comercial con una marca,
vivirá en otra tabla que el motor de matching no importa, y el test
`test_matching_has_no_commercial_inputs` fallará si alguien lo intenta.

El motivo no es purismo: es que un ranking que puede leer datos de ingresos
acaba optimizando ingresos. La separación tiene que ser estructural para que
sea creíble.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass

from ..routine.amounts import ProductCategory
from .ingredients import Function, FunctionProfile, Ingredient, function_profile, parse_inci


class HoldLevel(enum.Enum):
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"
    EXTRA_STRONG = "extra_strong"


class Weight(enum.Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    RICH = "rich"


class Level(enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SurfactantStrength(enum.Enum):
    NONE = "none"
    MILD = "mild"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass(frozen=True)
class Product:
    """Un producto del catálogo. Solo datos fácticos y derivados del INCI."""

    id: str
    brand: str
    name: str
    category: ProductCategory
    size_ml: float | None = None
    price_minor_units: int | None = None
    """Precio en la unidad mínima (céntimos). El precio se usa para presupuesto
    y coste por uso, **nunca** como señal de calidad (A15)."""
    currency: str = "EUR"
    available_in: tuple[str, ...] = ()
    ingredients: tuple[Ingredient, ...] = ()
    hold_level: HoldLevel = HoldLevel.NONE
    weight: Weight = Weight.MEDIUM
    protein_level: Level = Level.NONE
    humectant_level: Level = Level.NONE
    emollient_level: Level = Level.NONE
    surfactant_strength: SurfactantStrength = SurfactantStrength.NONE
    chelating: bool = False
    cationic: bool = False
    film_forming: bool = False
    uv_filter: bool = False
    anti_static: bool = False
    notes_keys: tuple[str, ...] = ()

    @classmethod
    def from_inci(cls, *, inci: str, **kwargs: object) -> Product:
        """Construye un producto derivando los atributos del INCI.

        Los atributos derivados son estimaciones a partir de la lista de
        ingredientes, no datos declarados por la marca. Se pueden sobrescribir
        pasándolos explícitamente.
        """
        ingredients = tuple(parse_inci(inci))
        derived = derive_attributes(ingredients)
        derived.update({k: v for k, v in kwargs.items() if v is not None})
        derived["ingredients"] = ingredients
        return cls(**derived)  # type: ignore[arg-type]

    @property
    def function_profile(self) -> FunctionProfile:
        return function_profile(self.ingredients)

    @property
    def price_per_ml(self) -> float | None:
        if self.price_minor_units is None or not self.size_ml:
            return None
        return self.price_minor_units / 100.0 / self.size_ml

    def attribute(self, name: str) -> object:
        return getattr(self, name, None)


def derive_attributes(ingredients: Sequence[Ingredient]) -> dict[str, object]:
    """Deriva atributos del perfil funcional de la formulación."""
    profile = function_profile(ingredients)

    protein = _level(profile.weight(Function.HYDROLYSED_PROTEIN), (0.01, 0.04, 0.09))
    humectant = _level(profile.weight(Function.HUMECTANT), (0.02, 0.07, 0.14))
    emollient = _level(
        profile.weight(Function.EMOLLIENT) + profile.weight(Function.OCCLUSIVE),
        (0.03, 0.09, 0.18),
    )

    anionic = profile.weight(Function.ANIONIC_SURFACTANT)
    amphoteric = profile.weight(Function.AMPHOTERIC_SURFACTANT)
    nonionic = profile.weight(Function.NONIONIC_SURFACTANT)
    if anionic >= 0.10:
        surfactant = SurfactantStrength.STRONG
    elif anionic >= 0.03:
        surfactant = SurfactantStrength.MEDIUM
    elif amphoteric + nonionic >= 0.03:
        surfactant = SurfactantStrength.MILD
    else:
        surfactant = SurfactantStrength.NONE

    film = profile.weight(Function.FILM_FORMER)
    if film >= 0.12:
        hold = HoldLevel.STRONG
    elif film >= 0.06:
        hold = HoldLevel.MEDIUM
    elif film >= 0.02:
        hold = HoldLevel.LIGHT
    else:
        hold = HoldLevel.NONE

    heaviness = profile.weight(Function.OCCLUSIVE) + profile.weight(Function.OIL_SEALING)
    if heaviness >= 0.12:
        weight = Weight.RICH
    elif heaviness >= 0.04:
        weight = Weight.MEDIUM
    else:
        weight = Weight.LIGHT

    return {
        "protein_level": protein,
        "humectant_level": humectant,
        "emollient_level": emollient,
        "surfactant_strength": surfactant,
        "hold_level": hold,
        "weight": weight,
        "chelating": profile.has(Function.CHELATOR, threshold=0.01),
        "cationic": profile.has(Function.CATIONIC_CONDITIONER, threshold=0.01),
        "film_forming": film >= 0.02,
        "uv_filter": profile.has(Function.UV_FILTER, threshold=0.005),
        "anti_static": profile.has(Function.CATIONIC_CONDITIONER, threshold=0.01),
    }


def _level(value: float, thresholds: tuple[float, float, float]) -> Level:
    low, medium, high = thresholds
    if value >= high:
        return Level.HIGH
    if value >= medium:
        return Level.MEDIUM
    if value >= low:
        return Level.LOW
    return Level.NONE


@dataclass
class InventoryItem:
    """Algo que la persona ya tiene. Es el punto de partida de todo (A15)."""

    id: str
    product: Product | None = None
    custom_name: str | None = None
    custom_category: ProductCategory | None = None
    custom_inci: str | None = None
    amount_left_ratio: float = 1.0
    opened_at: str | None = None
    pao_months: int | None = None
    """Period After Opening declarado en el envase (el símbolo del tarrito)."""
    disliked: bool = False
    notes: str | None = None

    @property
    def category(self) -> ProductCategory | None:
        if self.product is not None:
            return self.product.category
        return self.custom_category

    @property
    def display_name(self) -> str:
        if self.product is not None:
            return f"{self.product.brand} {self.product.name}"
        return self.custom_name or "?"

    @property
    def is_usable(self) -> bool:
        return self.amount_left_ratio > 0.05 and not self.disliked

    def as_product(self) -> Product | None:
        """Un artículo del inventario sin ficha de catálogo, pero con INCI
        escrito a mano, sigue siendo analizable."""
        if self.product is not None:
            return self.product
        if self.custom_inci and self.custom_category:
            return Product.from_inci(
                inci=self.custom_inci,
                id=f"custom:{self.id}",
                brand="",
                name=self.custom_name or "",
                category=self.custom_category,
            )
        return None
