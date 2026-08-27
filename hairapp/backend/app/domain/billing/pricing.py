"""Precio por país.

**Por qué existe este módulo.** Aplicar un precio en dólares tal cual a toda
LATAM deja el producto fuera de alcance en la mayoría de sus mercados. Un
precio que en EE. UU. es "un café" puede ser, en poder adquisitivo, entre tres
y seis veces más caro en México, Colombia o Argentina. Cobrar lo mismo en todas
partes no es neutralidad: es excluir.

Los niveles de aquí son **puntos de partida para validar**, no precios
definitivos. Están anclados a lo que cuesta un producto de cuidado capilar de
gama media en cada mercado, que es la comparación que la gente hace de verdad:
"¿esto vale menos que el acondicionador que compro?".

Las cifras se expresan en la unidad mínima de cada moneda (centavos), como en
el resto del sistema, para no arrastrar errores de coma flotante en dinero.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .entitlements import Plan


class Tier(enum.Enum):
    """Grupos de países con capacidad de pago parecida para una app.

    Agrupar evita mantener doscientas filas y evita también el error contrario:
    un precio único global.
    """

    NORTH_AMERICA = "north_america"
    LATAM_UPPER = "latam_upper"
    LATAM_MID = "latam_mid"
    LATAM_ACCESSIBLE = "latam_accessible"
    EUROPE = "europe"

    @property
    def label_key(self) -> str:
        return f"pricing.tier.{self.value}"


#: País -> nivel. Solo mercados de lanzamiento y adyacentes.
COUNTRY_TIER: dict[str, Tier] = {
    "US": Tier.NORTH_AMERICA,
    "CA": Tier.NORTH_AMERICA,
    "PR": Tier.NORTH_AMERICA,
    "CL": Tier.LATAM_UPPER,
    "UY": Tier.LATAM_UPPER,
    "PA": Tier.LATAM_UPPER,
    "CR": Tier.LATAM_UPPER,
    "MX": Tier.LATAM_MID,
    "BR": Tier.LATAM_MID,
    "AR": Tier.LATAM_MID,
    "CO": Tier.LATAM_MID,
    "PE": Tier.LATAM_MID,
    "EC": Tier.LATAM_MID,
    "DO": Tier.LATAM_MID,
    "GT": Tier.LATAM_ACCESSIBLE,
    "BO": Tier.LATAM_ACCESSIBLE,
    "PY": Tier.LATAM_ACCESSIBLE,
    "HN": Tier.LATAM_ACCESSIBLE,
    "NI": Tier.LATAM_ACCESSIBLE,
    "SV": Tier.LATAM_ACCESSIBLE,
    "VE": Tier.LATAM_ACCESSIBLE,
    "ES": Tier.EUROPE,
}

DEFAULT_TIER = Tier.LATAM_MID


@dataclass(frozen=True)
class Price:
    """Un precio concreto. `minor_units` para no perder céntimos."""

    monthly_minor_units: int
    annual_minor_units: int
    currency: str

    @property
    def annual_monthly_equivalent(self) -> float:
        return self.annual_minor_units / 12 / 100

    @property
    def annual_discount_ratio(self) -> float:
        """Cuánto se ahorra pagando al año.

        Es alto a propósito: el valor de este producto es longitudinal. Nos
        interesa alguien que acumule doce meses de diario, no que pruebe un mes.
        """
        yearly_at_monthly = self.monthly_minor_units * 12
        if yearly_at_monthly == 0:
            return 0.0
        return 1 - (self.annual_minor_units / yearly_at_monthly)

    def as_dict(self) -> dict[str, object]:
        return {
            "monthly_minor_units": self.monthly_minor_units,
            "annual_minor_units": self.annual_minor_units,
            "currency": self.currency,
            "annual_discount_ratio": round(self.annual_discount_ratio, 3),
        }


#: Precios de partida por nivel, para el plan Estudio.
#: Anclados a "menos que un acondicionador de gama media en ese mercado".
_STUDIO_PRICES: dict[Tier, Price] = {
    Tier.NORTH_AMERICA: Price(499, 3499, "USD"),
    Tier.EUROPE: Price(499, 3499, "EUR"),
    Tier.LATAM_UPPER: Price(349, 2499, "USD"),
    Tier.LATAM_MID: Price(249, 1799, "USD"),
    Tier.LATAM_ACCESSIBLE: Price(149, 1099, "USD"),
}

#: Trichon Pro no es autoservicio: se contrata hablando con nosotros, así que
#: no lleva precio de tienda.
_PRO_TIERS: frozenset[Tier] = frozenset()


def tier_for(country: str | None) -> Tier:
    if not country:
        return DEFAULT_TIER
    return COUNTRY_TIER.get(country.upper(), DEFAULT_TIER)


def price_for(plan: Plan, country: str | None) -> Price | None:
    """Precio de un plan en un país. `None` si ese plan no se vende ahí."""
    if plan is not Plan.STUDIO:
        return None
    return _STUDIO_PRICES[tier_for(country)]


def catalogue() -> list[dict[str, object]]:
    """Todos los niveles, para revisar la escala de un vistazo."""
    return [
        {
            "tier": tier.value,
            "label_key": tier.label_key,
            "countries": sorted(c for c, t in COUNTRY_TIER.items() if t is tier),
            "studio": price.as_dict(),
        }
        for tier, price in _STUDIO_PRICES.items()
    ]
