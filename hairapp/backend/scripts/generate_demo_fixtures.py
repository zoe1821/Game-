"""Genera los datos de demostración de la app ejecutando el motor real.

No son datos inventados a mano: se construye un perfil realista, se pasa por
el mismo motor que usa la API, y se congela su salida. Así lo que se ve en
modo demostración es exactamente lo que el sistema produce, con sus
explicaciones, sus confianzas y sus incertidumbres reales.
"""

from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta

from app.domain.climate.weather import Weather, forecast
from app.domain.evidence.language import ControlledLanguage
from app.domain.hair.attributes import (
    CurlPattern,
    Density,
    Porosity,
    ProcessingState,
    StrandDiameter,
)
from app.domain.hair.growth import LengthObservation, read_growth
from app.domain.hair.zones import ALL_ZONES, Zone
from app.domain.learning.cold_start import guidance
from app.domain.learning.journal import JournalEntry, ResultRating, analyse_journal
from app.domain.rules.engine import RuleEngine
from app.domain.rules.loader import load_all
from app.domain.rules.model import RuleKind
from app.domain.routine.generator import (
    Goal,
    RoutineContext,
    RoutineGenerator,
    RoutineKind,
    ZoneState,
)
from app.domain.twin.model import build_twin
from app.domain.twin.projection import Scenario, project

OUT = pathlib.Path("../mobile/src/demo/fixtures.json")

# --- perfil de ejemplo ----------------------------------------------------
# Una cabeza real: coronilla más porosa y con color, nuca virgen y más cerrada,
# puntas con daño visible. Es justo el caso que el producto existe para tratar
# y que una app de "tu tipo de rizo" no puede representar.
ZONE_SETUP = {
    "crown": (CurlPattern.CURLY_3A, Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, ProcessingState.COLOURED, 28.0),
    "back_crown": (CurlPattern.CURLY_3A, Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, ProcessingState.COLOURED, 30.0),
    "nape": (CurlPattern.CURLY_3C, Porosity.MEDIUM, Density.HIGH, StrandDiameter.MEDIUM, ProcessingState.VIRGIN, 32.0),
    "occipital": (CurlPattern.CURLY_3C, Porosity.MEDIUM, Density.HIGH, StrandDiameter.MEDIUM, ProcessingState.VIRGIN, 32.0),
    "ends": (CurlPattern.CURLY_3B, Porosity.HIGH, Density.MEDIUM, StrandDiameter.FINE, ProcessingState.COLOURED, 32.0),
}
DEFAULT = (CurlPattern.CURLY_3B, Porosity.MEDIUM, Density.MEDIUM, StrandDiameter.MEDIUM, ProcessingState.VIRGIN, 30.0)


def zone_states() -> list[ZoneState]:
    states = []
    for zone in ALL_ZONES:
        pattern, porosity, density, diameter, processing, length = ZONE_SETUP.get(zone.value, DEFAULT)
        states.append(
            ZoneState(
                zone=zone,
                pattern=pattern,
                porosity=porosity,
                density=density,
                strand_diameter=diameter,
                processing=processing,
                length_cm=length,
                damage_signs=("split_ends", "breakage") if zone is Zone.ENDS else (),
            )
        )
    return states


def measured(value: str, confidence: float, source: str) -> dict:
    return {"value": value, "confidence": confidence, "source": source, "observed_at": None, "notes": None}


def zones_payload() -> list[dict]:
    out = []
    for zone in ALL_ZONES:
        pattern, porosity, density, diameter, processing, length = ZONE_SETUP.get(zone.value, DEFAULT)
        known = zone.value in ZONE_SETUP
        measurements = {
            "pattern": measured(pattern.value, 1.0 if known else 0.45, "user" if known else "inferred"),
            "porosity": measured(porosity.value, 0.62 if known else 0.0, "inferred" if known else "default"),
            "density": measured(density.value, 0.55, "inferred"),
            "strand_diameter": measured(diameter.value, 0.6, "inferred"),
            "processing": measured(processing.value, 1.0, "user"),
            "length_cm": {"value": length, "confidence": 1.0, "source": "user", "observed_at": None, "notes": None},
        }
        if not known:
            # Zonas que no se fotografiaron: se muestran con lo poco que se sabe.
            measurements = {"pattern": measurements["pattern"], "length_cm": measurements["length_cm"]}
        out.append({
            "zone": zone.value,
            "label_key": zone.label_key,
            "measurements": measurements,
            "damage_signs": ["split_ends", "breakage"] if zone is Zone.ENDS else [],
            "notes": None,
            "completeness": round(len(measurements) / 14, 3),
        })
    return out


def journal_entries() -> list[JournalEntry]:
    base = date.today() - timedelta(days=7 * 12)
    R = ResultRating
    plan = [
        (8.0, R.GREAT, R.GOOD, ("gel-fuerte", "crema")), (11.0, R.GREAT, R.GREAT, ("gel-fuerte", "crema")),
        (14.0, R.GOOD, R.GOOD, ("gel-fuerte", "crema")), (19.0, R.GOOD, R.MEH, ("gel-fuerte", "crema")),
        (22.0, R.MEH, R.MEH, ("gel-suave",)), (24.0, R.MEH, R.BAD, ("gel-suave",)),
        (21.0, R.MEH, R.MEH, ("gel-suave",)), (16.0, R.GOOD, R.MEH, ("gel-suave",)),
        (12.0, R.GREAT, R.GOOD, ("gel-fuerte", "crema")), (9.0, R.GREAT, R.GREAT, ("gel-fuerte", "crema")),
        (13.0, R.GOOD, R.GOOD, ("gel-fuerte", "crema")), (18.0, R.GOOD, R.MEH, ("gel-suave",)),
    ]
    return [
        JournalEntry(
            id=f"demo-{i}", date=base + timedelta(days=7 * i), product_ids=prods,
            technique_ids=("praying_hands", "diffusing"), dew_point_c=dew,
            rating_day1=d1, rating_day2=d2,
            amounts_ml={"gel": 6.0 + (i % 3)},
        )
        for i, (dew, d1, d2) in enumerate([(p[0], p[1], p[2]) for p in plan])
        for prods in [plan[i][3]]
    ]


def main() -> None:
    engine = RuleEngine(load_all(language=ControlledLanguage.load()))
    generator = RoutineGenerator(engine)
    entries = journal_entries()

    context = RoutineContext(
        zones=zone_states(),
        goals=[Goal.DEFINITION, Goal.DAMAGE_RECOVERY, Goal.FRIZZ_CONTROL],
        weather={"temperature_c": 26.0, "relative_humidity": 72.0, "dew_point_c": 20.5, "uv_index": 8.0},
        water_hardness_ppm=210.0,
        uses_heat=True,
        owns_diffuser=True,
    )
    routine = generator.generate(context)
    quick = generator.generate(
        RoutineContext(zones=zone_states(), goals=[Goal.DEFINITION], kind=RoutineKind.QUICK_10)
    )

    findings = analyse_journal(entries)
    twin = build_twin(profile_id="demo", entries=entries, findings=findings)
    projections = {s.value: project(twin, s).as_dict() for s in Scenario}

    growth = read_growth([
        LengthObservation(date.today() - timedelta(days=240), 26.0),
        LengthObservation(date.today() - timedelta(days=120), 28.0),
        LengthObservation(date.today(), 29.0, trimmed_cm=1.0),
    ])

    payload = {
        "generated_note": "Generado ejecutando el motor real, no escrito a mano.",
        "profile": {
            "id": "demo", "depth_level": "intermediate", "completeness": 0.68,
            "onboarding_essential_done": True, "wash_frequency_days": 4.0, "country": "MX",
            "water_hardness_ppm": 210.0, "uses_heat": True, "owns_diffuser": True,
            "protective_style": "none",
            "goals": ["definition", "damage_recovery", "frizz_control"],
            "zones": zones_payload(),
        },
        "zones": zones_payload(),
        "routine": routine.as_dict(),
        "routine_quick": quick.as_dict(),
        "myths": [
            {
                "id": r.id, "myth": str(r.outcome.get("myth", "")), "message_key": r.message_key,
                "correction_key": str(r.outcome.get("correction_key", "")),
                "related_concept": str(r.outcome.get("related_concept", "")),
                "mechanism": r.mechanism, "evidence_level": r.evidence_level.value,
                "evidence_label_key": r.evidence_level.label_key, "tags": list(r.tags),
            }
            for r in engine.rules if r.kind is RuleKind.MYTH
        ],
        "rules": [
            {
                "id": r.id, "kind": r.kind.value, "evidence_level": r.evidence_level.value,
                "evidence_label_key": r.evidence_level.label_key,
                "evidence_confidence": r.evidence_level.confidence,
                "mechanism": r.mechanism, "sources": list(r.sources), "tags": list(r.tags),
            }
            for r in engine.rules
        ],
        "journal": [
            {
                "id": e.id, "date": e.date.isoformat(), "product_ids": list(e.product_ids),
                "technique_ids": list(e.technique_ids), "amounts_ml": dict(e.amounts_ml),
                "weather": {"dew_point_c": e.dew_point_c or 0.0},
                "ratings": {
                    k: v.value for k, v in
                    [("day1", e.rating_day1), ("day2", e.rating_day2)] if v is not None
                },
                "notes": None, "experiment_arm_id": None, "longevity_days": e.longevity_days,
            }
            for e in reversed(entries)
        ],
        "insights": {
            "entry_count": len(entries),
            "findings": [f.as_dict() for f in findings],
            "has_enough_data": bool(findings),
            "message_key": "learning.findings_available" if findings else "learning.still_learning_about_you",
        },
        "twin": twin.as_dict(),
        "projections": projections,
        "growth": {"has_reading": True, **growth.as_dict()} if growth else {"has_reading": False},
        "forecast": forecast(Weather(26.0, 72.0, uv_index=8.0), porosity="high").as_dict(),
        "cold_start": guidance(entry_count=len(entries), pattern_family="3").as_dict(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escrito {OUT} ({OUT.stat().st_size // 1024} KB)")
    print(f"  rutina: {len(payload['routine']['steps'])} pasos")
    print(f"  mitos: {len(payload['myths'])} | reglas: {len(payload['rules'])}")
    print(f"  diario: {len(payload['journal'])} | hallazgos: {len(payload['insights']['findings'])}")
    print(f"  twin: {payload['twin']['completeness']:.0%} conocido")


if __name__ == "__main__":
    main()
