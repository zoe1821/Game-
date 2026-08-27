"""Vocabulario de propiedades capilares.

Nota de diseño (A5): el curl typing 1a-4c se soporta porque la gente lo usa y
lo busca, pero se trata como **una clasificación descriptiva y limitada**. Las
propiedades realmente accionables son las métricas continuas: diámetro de rizo,
frecuencia de curva, uniformidad, elongación, clumping y frizz superficial.
El motor de rutinas usa esas, no el tipo.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from ..common import Measured


class CurlPattern(enum.Enum):
    """Clasificación descriptiva 1a-4c. Ver nota del módulo."""

    STRAIGHT_1A = "1a"
    STRAIGHT_1B = "1b"
    STRAIGHT_1C = "1c"
    WAVY_2A = "2a"
    WAVY_2B = "2b"
    WAVY_2C = "2c"
    CURLY_3A = "3a"
    CURLY_3B = "3b"
    CURLY_3C = "3c"
    COILY_4A = "4a"
    COILY_4B = "4b"
    COILY_4C = "4c"

    @property
    def family(self) -> PatternFamily:
        return PatternFamily(self.value[0])

    @property
    def approx_curl_diameter_mm(self) -> tuple[float, float]:
        """Rango orientativo de diámetro de rizo, en mm.

        Orientativo de verdad: los rangos publicados varían entre fuentes y no
        hay un estándar cerrado. Se usa solo para traducir una medición de
        imagen a un tipo aproximado, nunca al revés.
        """
        return _CURL_DIAMETER_RANGES[self]


class PatternFamily(enum.Enum):
    STRAIGHT = "1"
    WAVY = "2"
    CURLY = "3"
    COILY = "4"


_CURL_DIAMETER_RANGES: dict[CurlPattern, tuple[float, float]] = {
    CurlPattern.STRAIGHT_1A: (float("inf"), float("inf")),
    CurlPattern.STRAIGHT_1B: (120.0, float("inf")),
    CurlPattern.STRAIGHT_1C: (80.0, 120.0),
    CurlPattern.WAVY_2A: (50.0, 80.0),
    CurlPattern.WAVY_2B: (38.0, 50.0),
    CurlPattern.WAVY_2C: (28.0, 38.0),
    CurlPattern.CURLY_3A: (18.0, 28.0),
    CurlPattern.CURLY_3B: (12.0, 18.0),
    CurlPattern.CURLY_3C: (8.0, 12.0),
    CurlPattern.COILY_4A: (5.0, 8.0),
    CurlPattern.COILY_4B: (3.0, 5.0),
    CurlPattern.COILY_4C: (0.0, 3.0),
}


def pattern_from_curl_diameter(diameter_mm: float) -> CurlPattern:
    """Traduce un diámetro de rizo medido a la clasificación más cercana."""
    for pattern, (low, high) in _CURL_DIAMETER_RANGES.items():
        if low <= diameter_mm < high:
            return pattern
    return CurlPattern.STRAIGHT_1A


class Porosity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MIXED = "mixed"
    """Raíz y puntas con porosidad distinta: lo más común en cabello procesado."""


class Density(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StrandDiameter(enum.Enum):
    FINE = "fine"
    MEDIUM = "medium"
    COARSE = "coarse"


class Elasticity(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    EXCESSIVE = "excessive"
    """Se estira mucho y no recupera: se lee con cautela, nunca como orden de
    'aplicar proteína ya' (ver reglas con condición de daño y porosidad)."""


class ProcessingState(enum.Enum):
    VIRGIN = "virgin"
    COLOURED = "coloured"
    BLEACHED = "bleached"
    HIGHLIGHTED = "highlighted"
    RELAXED = "relaxed"
    PERMED = "permed"
    KERATIN_TREATED = "keratin_treated"
    CHEMICALLY_STRAIGHTENED = "chemically_straightened"
    TRANSITIONING = "transitioning"
    """En transición química: raíz virgen y largos procesados conviviendo."""

    @property
    def is_chemically_processed(self) -> bool:
        return self is not ProcessingState.VIRGIN


class DamageSign(enum.Enum):
    """Solo signos **visibles**. Nunca se afirma daño interno de la fibra a
    partir de una foto (A7, docs/09-CONTROLLED-LANGUAGE.md)."""

    SPLIT_ENDS = "split_ends"
    WHITE_DOTS = "white_dots"
    BREAKAGE = "breakage"
    MID_SHAFT_SPLITS = "mid_shaft_splits"
    FAIRY_KNOTS = "fairy_knots"
    ROUGH_TEXTURE = "rough_texture"
    HEAT_ALTERED_PATTERN = "heat_altered_pattern"
    CHEMICAL_ALTERED_PATTERN = "chemical_altered_pattern"
    GUMMY_WHEN_WET = "gummy_when_wet"
    EXCESSIVE_TANGLING = "excessive_tangling"


class ScalpObservation(enum.Enum):
    """Observaciones visibles del cuero cabelludo. El vocabulario evita
    cualquier término con implicación médica por diseño."""

    BUILDUP = "buildup"
    VISIBLE_OIL = "visible_oil"
    FLAKING = "flaking"
    VISIBLE_REDNESS = "visible_redness"
    TIGHTNESS_REPORTED = "tightness_reported"
    ITCH_REPORTED = "itch_reported"


class ReferralSign(enum.Enum):
    """Señales ante las que la app deja de interpretar y deriva (A23).

    No se estima nada a partir de ellas: se muestra el bloque de derivación
    completo y se detiene el análisis de esa zona.
    """

    OPEN_WOUND = "open_wound"
    INFLAMMATION = "inflammation"
    SUDDEN_LOCALISED_LOSS = "sudden_localised_loss"
    PERSISTENT_PAIN = "persistent_pain"
    BLEEDING = "bleeding"
    RAPID_UNEXPLAINED_CHANGE = "rapid_unexplained_change"


class ProtectiveStyle(enum.Enum):
    NONE = "none"
    BRAIDS = "braids"
    TWISTS = "twists"
    LOCS = "locs"
    WIG = "wig"
    WEAVE = "weave"
    EXTENSIONS = "extensions"
    BUN = "bun"
    THREADING = "threading"


@dataclass
class ZoneProfile:
    """Estado de una zona del mapa capilar.

    Todos los campos estimados son `Measured`: sin procedencia no entran.
    """

    zone: object  # Zone; se tipa laxo para no crear un import circular
    pattern: Measured[CurlPattern] | None = None
    curl_diameter_mm: Measured[float] | None = None
    curve_frequency_per_cm: Measured[float] | None = None
    strand_diameter: Measured[StrandDiameter] | None = None
    density: Measured[Density] | None = None
    porosity: Measured[Porosity] | None = None
    elasticity: Measured[Elasticity] | None = None
    frizz_level: Measured[float] | None = None
    definition_level: Measured[float] | None = None
    uniformity: Measured[float] | None = None
    clumping: Measured[float] | None = None
    shrinkage_ratio: Measured[float] | None = None
    length_cm: Measured[float] | None = None
    processing: Measured[ProcessingState] | None = None
    damage_signs: list[DamageSign] = field(default_factory=list)
    notes: str | None = None

    def measured_fields(self) -> dict[str, Measured[object]]:
        out: dict[str, Measured[object]] = {}
        for name, value in vars(self).items():
            if isinstance(value, Measured):
                out[name] = value
        return out

    @property
    def completeness(self) -> float:
        """Fracción de propiedades estimables que ya tienen valor."""
        return len(self.measured_fields()) / _ESTIMABLE_FIELD_COUNT


_ESTIMABLE_FIELD_COUNT = 14
