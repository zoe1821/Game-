"""Mapa capilar por zonas (A4).

La zona es la unidad de análisis **y** la unidad de instrucción: la rutina no
dice "aplica crema", dice "aplica crema en la coronilla" con cantidad y técnica
propias. Es el primer pilar de diferenciación (docs/03-POSITIONING.md §2).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Zone(enum.Enum):
    FRONTAL_HAIRLINE = "frontal_hairline"
    BANGS = "bangs"
    FRONT_LEFT = "front_left"
    FRONT_RIGHT = "front_right"
    LEFT_TEMPLE = "left_temple"
    RIGHT_TEMPLE = "right_temple"
    SIDE_UPPER_LEFT = "side_upper_left"
    SIDE_UPPER_RIGHT = "side_upper_right"
    SIDE_LOWER_LEFT = "side_lower_left"
    SIDE_LOWER_RIGHT = "side_lower_right"
    CROWN = "crown"
    BACK_CROWN = "back_crown"
    OCCIPITAL = "occipital"
    NAPE = "nape"
    ENDS = "ends"

    @property
    def label_key(self) -> str:
        return f"zone.{self.value}"


#: Todas las zonas del mapa. `ENDS` es transversal (las puntas de todo el
#: cabello), el resto son regiones del cuero cabelludo hacia el largo.
ALL_ZONES: tuple[Zone, ...] = tuple(Zone)

SCALP_ZONES: tuple[Zone, ...] = tuple(z for z in Zone if z is not Zone.ENDS)


class ZoneGroup(enum.Enum):
    """Agrupaciones útiles para instrucciones y para el modo rápido."""

    FRONT = "front"
    SIDES = "sides"
    TOP = "top"
    BACK = "back"
    ENDS = "ends"


ZONE_GROUPS: dict[ZoneGroup, tuple[Zone, ...]] = {
    ZoneGroup.FRONT: (
        Zone.FRONTAL_HAIRLINE,
        Zone.BANGS,
        Zone.FRONT_LEFT,
        Zone.FRONT_RIGHT,
    ),
    ZoneGroup.SIDES: (
        Zone.LEFT_TEMPLE,
        Zone.RIGHT_TEMPLE,
        Zone.SIDE_UPPER_LEFT,
        Zone.SIDE_UPPER_RIGHT,
        Zone.SIDE_LOWER_LEFT,
        Zone.SIDE_LOWER_RIGHT,
    ),
    ZoneGroup.TOP: (Zone.CROWN, Zone.BACK_CROWN),
    ZoneGroup.BACK: (Zone.OCCIPITAL, Zone.NAPE),
    ZoneGroup.ENDS: (Zone.ENDS,),
}


def group_of(zone: Zone) -> ZoneGroup:
    for group, zones in ZONE_GROUPS.items():
        if zone in zones:
            return group
    raise KeyError(zone)


class PhotoAngle(enum.Enum):
    """Ángulos que pide el flujo de scan (A3)."""

    FRONT = "front"
    CROWN_TOP = "crown_top"
    LEFT_SIDE = "left_side"
    RIGHT_SIDE = "right_side"
    BACK = "back"
    NAPE = "nape"
    ENDS_CLOSEUP = "ends_closeup"
    STRAND_CLOSEUP = "strand_closeup"

    @property
    def is_required(self) -> bool:
        return self in _REQUIRED_ANGLES


_REQUIRED_ANGLES = frozenset(
    {
        PhotoAngle.FRONT,
        PhotoAngle.CROWN_TOP,
        PhotoAngle.LEFT_SIDE,
        PhotoAngle.BACK,
        PhotoAngle.ENDS_CLOSEUP,
    }
)

#: Qué zonas puede observar cada ángulo. Sin esto no hay forma honesta de decir
#: "esta zona no la vimos" en vez de estimarla igualmente.
ANGLE_COVERAGE: dict[PhotoAngle, tuple[Zone, ...]] = {
    PhotoAngle.FRONT: (
        Zone.FRONTAL_HAIRLINE,
        Zone.BANGS,
        Zone.FRONT_LEFT,
        Zone.FRONT_RIGHT,
        Zone.LEFT_TEMPLE,
        Zone.RIGHT_TEMPLE,
    ),
    PhotoAngle.CROWN_TOP: (Zone.CROWN, Zone.BACK_CROWN, Zone.FRONTAL_HAIRLINE),
    PhotoAngle.LEFT_SIDE: (
        Zone.LEFT_TEMPLE,
        Zone.SIDE_UPPER_LEFT,
        Zone.SIDE_LOWER_LEFT,
        Zone.FRONT_LEFT,
    ),
    PhotoAngle.RIGHT_SIDE: (
        Zone.RIGHT_TEMPLE,
        Zone.SIDE_UPPER_RIGHT,
        Zone.SIDE_LOWER_RIGHT,
        Zone.FRONT_RIGHT,
    ),
    PhotoAngle.BACK: (Zone.BACK_CROWN, Zone.OCCIPITAL, Zone.NAPE),
    PhotoAngle.NAPE: (Zone.NAPE, Zone.OCCIPITAL),
    PhotoAngle.ENDS_CLOSEUP: (Zone.ENDS,),
    PhotoAngle.STRAND_CLOSEUP: (Zone.ENDS,),
}


@dataclass(frozen=True)
class ZoneCoverage:
    """Qué zonas quedaron cubiertas por un set de fotos y cuáles no."""

    covered: frozenset[Zone]
    uncovered: frozenset[Zone]

    @property
    def is_complete(self) -> bool:
        return not self.uncovered


def coverage_for(angles: list[PhotoAngle]) -> ZoneCoverage:
    covered: set[Zone] = set()
    for angle in angles:
        covered.update(ANGLE_COVERAGE.get(angle, ()))
    return ZoneCoverage(
        covered=frozenset(covered),
        uncovered=frozenset(set(ALL_ZONES) - covered),
    )
