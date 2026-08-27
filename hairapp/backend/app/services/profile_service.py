"""Orquestación del perfil capilar: DB + dominio.

Aquí vive la regla más importante del producto en su forma ejecutable: una
corrección manual **nunca** se sobrescribe con una estimación automática, y la
estimación desplazada se archiva en vez de perderse.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.base import utcnow
from ..domain.common import Measured, Source, resolve
from ..domain.hair.zones import ALL_ZONES, Zone
from ..models.hair import HairProfile, HairZone, ZoneMeasurementHistory

#: Campos de zona que la app puede estimar y la persona corregir.
MEASURABLE_FIELDS = (
    "pattern",
    "curl_diameter_mm",
    "curve_frequency_per_cm",
    "strand_diameter",
    "density",
    "porosity",
    "elasticity",
    "frizz_level",
    "definition_level",
    "uniformity",
    "clumping",
    "shrinkage_ratio",
    "length_cm",
    "processing",
)


def ensure_zones(session: Session, profile: HairProfile) -> list[HairZone]:
    """Crea las 15 zonas si faltan. El mapa existe siempre, aunque esté vacío."""
    existing = {zone.zone for zone in profile.zones}
    created: list[HairZone] = []
    for zone in ALL_ZONES:
        if zone in existing:
            continue
        row = HairZone(profile_id=profile.id, zone=zone, measurements={}, damage_signs=[])
        session.add(row)
        created.append(row)
    if created:
        session.flush()
        session.refresh(profile)
    return list(profile.zones)


def serialise_measured(measured: Measured[Any]) -> dict[str, Any]:
    value = measured.value
    return {
        "value": value.value if hasattr(value, "value") else value,
        "confidence": round(measured.confidence, 4),
        "source": measured.source.value,
        "observed_at": measured.observed_at.isoformat() if measured.observed_at else None,
        "notes": measured.notes,
    }


def deserialise_measured(payload: Mapping[str, Any]) -> Measured[Any]:
    observed = payload.get("observed_at")
    return Measured(
        value=payload["value"],
        source=Source(payload["source"]),
        confidence=float(payload["confidence"]),
        observed_at=date.fromisoformat(observed) if observed else None,
        notes=payload.get("notes"),
    )


def apply_estimates(
    session: Session,
    zone_row: HairZone,
    estimates: Mapping[str, Measured[Any]],
    *,
    now: datetime | None = None,
) -> dict[str, str]:
    """Aplica estimaciones automáticas a una zona.

    Devuelve, por campo, qué pasó: `applied`, `kept_user_value` o
    `kept_stronger`. Ese detalle sube hasta la UI: la persona ve que su
    corrección se respetó, en vez de tener que confiar en que así fue.
    """
    timestamp = now or utcnow()
    measurements = dict(zone_row.measurements)
    outcomes: dict[str, str] = {}

    for field, incoming in estimates.items():
        if field not in MEASURABLE_FIELDS:
            continue
        current_payload = measurements.get(field)
        if current_payload is None:
            measurements[field] = serialise_measured(incoming)
            outcomes[field] = "applied"
            continue

        current = deserialise_measured(current_payload)
        if current.is_user_confirmed:
            # A1.4. Esto es la línea que no se cruza.
            outcomes[field] = "kept_user_value"
            continue

        # Una estimación nueva sustituye a la anterior salvo que la anterior
        # sea estrictamente más fuerte. El empate lo gana la nueva: cuando la
        # persona vuelve a responder el onboarding, está actualizando su
        # respuesta, no compitiendo consigo misma.
        stronger = resolve([incoming, current])
        if stronger is incoming:
            session.add(
                ZoneMeasurementHistory(
                    zone_row_id=zone_row.id,
                    field=field,
                    payload=current_payload,
                    replaced_at=timestamp,
                )
            )
            measurements[field] = serialise_measured(incoming)
            outcomes[field] = "applied"
        else:
            outcomes[field] = "kept_stronger"

    zone_row.measurements = measurements
    session.add(zone_row)
    return outcomes


def set_user_value(
    session: Session,
    zone_row: HairZone,
    field: str,
    value: Any,
    *,
    now: datetime | None = None,
) -> None:
    """La persona corrige un valor. A partir de aquí es definitivo."""
    if field not in MEASURABLE_FIELDS:
        raise ValueError(f"campo no estimable: {field}")

    timestamp = now or utcnow()
    measurements = dict(zone_row.measurements)
    previous = measurements.get(field)
    if previous is not None:
        session.add(
            ZoneMeasurementHistory(
                zone_row_id=zone_row.id,
                field=field,
                payload=previous,
                replaced_at=timestamp,
            )
        )
    measurements[field] = {
        "value": value.value if hasattr(value, "value") else value,
        "confidence": 1.0,
        "source": Source.USER.value,
        "observed_at": timestamp.date().isoformat(),
        "notes": None,
    }
    zone_row.measurements = measurements
    session.add(zone_row)


def compute_completeness(profile: HairProfile) -> float:
    """Cuánto del perfil está relleno (B3: indicador sin presión agresiva)."""
    total = len(ALL_ZONES) * len(MEASURABLE_FIELDS)
    if total == 0:
        return 0.0
    filled = sum(
        1
        for zone in profile.zones
        for field in MEASURABLE_FIELDS
        if field in zone.measurements
    )
    zone_share = filled / total

    profile_signals = [
        profile.wash_frequency_days is not None,
        profile.country is not None,
        profile.water_hardness_ppm is not None,
        bool(profile.habits),
        bool(profile.goals),
    ]
    profile_share = sum(profile_signals) / len(profile_signals)

    return round(0.7 * zone_share + 0.3 * profile_share, 4)


def get_zone(session: Session, profile_id: str, zone: Zone) -> HairZone | None:
    return session.execute(
        select(HairZone).where(HairZone.profile_id == profile_id, HairZone.zone == zone)
    ).scalar_one_or_none()


def zone_states(profile: HairProfile) -> list[dict[str, Any]]:
    """Zonas en forma plana, lista para construir el contexto de rutina."""
    states: list[dict[str, Any]] = []
    for zone_row in profile.zones:
        flat: dict[str, Any] = {"zone": zone_row.zone, "damage_signs": tuple(zone_row.damage_signs)}
        confidences: dict[str, float] = {}
        for field, payload in zone_row.measurements.items():
            flat[field] = payload["value"]
            confidences[field] = payload["confidence"]
        flat["confidence_by_field"] = confidences
        states.append(flat)
    return states


def iter_measured(zone_row: HairZone) -> Iterable[tuple[str, Measured[Any]]]:
    for field, payload in zone_row.measurements.items():
        yield field, deserialise_measured(payload)
