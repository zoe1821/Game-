"""Clima y dureza del agua (A12).

El punto de rocío, no la humedad relativa, es lo que predice el comportamiento
del cabello: la humedad relativa al 80 % a 5 °C y al 80 % a 28 °C describen
cantidades de agua en el aire completamente distintas. El punto de rocío mide
agua absoluta, que es lo que la fibra intercambia.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass

from ..common import Explanation, clamp


@dataclass(frozen=True)
class Weather:
    temperature_c: float
    relative_humidity: float
    """0-100."""
    uv_index: float | None = None
    wind_kph: float | None = None

    @property
    def dew_point_c(self) -> float:
        """Punto de rocío por la aproximación de Magnus-Tetens.

        Se calcula en vez de pedirlo al proveedor porque no todos lo dan y la
        aproximación es buena en el rango de temperaturas habitables.
        """
        a, b = 17.62, 243.12
        rh = max(1.0, min(100.0, self.relative_humidity))
        gamma = math.log(rh / 100.0) + (a * self.temperature_c) / (b + self.temperature_c)
        return (b * gamma) / (a - gamma)


class DewPointBand(enum.Enum):
    VERY_DRY = "very_dry"
    DRY = "dry"
    COMFORTABLE = "comfortable"
    HUMID = "humid"
    VERY_HUMID = "very_humid"

    @property
    def label_key(self) -> str:
        return f"weather.dew_point.{self.value}"


#: Cortes en °C. Son convenciones meteorológicas de confort, reutilizadas aquí
#: porque describen bien la cantidad de agua disponible para la fibra.
_BANDS: tuple[tuple[float, DewPointBand], ...] = (
    (0.0, DewPointBand.VERY_DRY),
    (10.0, DewPointBand.DRY),
    (16.0, DewPointBand.COMFORTABLE),
    (21.0, DewPointBand.HUMID),
    (float("inf"), DewPointBand.VERY_HUMID),
)


def dew_point_band(dew_point_c: float) -> DewPointBand:
    for ceiling, band in _BANDS:
        if dew_point_c < ceiling:
            return band
    return DewPointBand.VERY_HUMID


@dataclass(frozen=True)
class HairForecast:
    """Pronóstico capilar (A12). Probabilidades, no certezas."""

    band: DewPointBand
    dew_point_c: float
    frizz_risk: float
    """0-1. Riesgo de frizz por intercambio de humedad, no una predicción."""
    dryness_risk: float
    uv_risk: float
    advice_keys: tuple[str, ...]
    explanation: Explanation

    def as_dict(self) -> dict[str, object]:
        return {
            "band": self.band.value,
            "dew_point_c": round(self.dew_point_c, 1),
            "frizz_risk": round(self.frizz_risk, 2),
            "dryness_risk": round(self.dryness_risk, 2),
            "uv_risk": round(self.uv_risk, 2),
            "advice_keys": list(self.advice_keys),
            "explanation": self.explanation.as_dict(),
        }


def forecast(
    weather: Weather,
    *,
    porosity: str | None = None,
    uses_humectants: bool = True,
) -> HairForecast:
    dew = weather.dew_point_c
    band = dew_point_band(dew)

    # El riesgo de frizz crece con el agua disponible en el aire, y lo hace más
    # rápido en porosidad alta porque la fibra la absorbe con menos resistencia.
    base_frizz = clamp((dew - 10.0) / 15.0)
    porosity_factor = {"high": 1.3, "mixed": 1.2, "medium": 1.0, "low": 0.8}.get(porosity or "", 1.0)
    humectant_factor = 1.2 if uses_humectants else 1.0
    frizz = clamp(base_frizz * porosity_factor * humectant_factor)

    # La sequedad va al revés y se agrava con el viento.
    base_dryness = clamp((10.0 - dew) / 15.0)
    wind_factor = 1.0 + clamp((weather.wind_kph or 0.0) / 60.0) * 0.3
    dryness = clamp(base_dryness * wind_factor)

    uv = clamp((weather.uv_index or 0.0) / 11.0)

    advice: list[str] = []
    if band in {DewPointBand.HUMID, DewPointBand.VERY_HUMID}:
        advice.append("weather.advice.reduce_humectants")
        advice.append("weather.advice.increase_film_forming")
    if band in {DewPointBand.DRY, DewPointBand.VERY_DRY}:
        advice.append("weather.advice.increase_emollients")
        advice.append("weather.advice.humectants_may_backfire")
    if uv >= 0.6:
        advice.append("weather.advice.uv_cover_or_filter")
    if (weather.wind_kph or 0) > 30:
        advice.append("weather.advice.protective_style_for_wind")
    if not advice:
        advice.append("weather.advice.no_adjustment_needed")

    explanation = Explanation(
        summary_key="weather.forecast.why",
        inputs_used=("input.weather", "input.porosity", "input.routine_humectants"),
        observations=(f"dew_point_c={dew:.1f}", f"band={band.value}"),
        evidence_level="professional_consensus",
        evidence_confidence=0.70,
        personal_confidence=0.0,
        sample_size=0,
        uncertainty_keys=("uncertainty.weather_is_not_your_history",),
        params={"porosity": porosity, "uses_humectants": uses_humectants},
    )

    return HairForecast(
        band=band,
        dew_point_c=dew,
        frizz_risk=frizz,
        dryness_risk=dryness,
        uv_risk=uv,
        advice_keys=tuple(advice),
        explanation=explanation,
    )


class WaterHardness(enum.Enum):
    SOFT = "soft"
    MODERATELY_HARD = "moderately_hard"
    HARD = "hard"
    VERY_HARD = "very_hard"

    @property
    def label_key(self) -> str:
        return f"water.hardness.{self.value}"


#: Cortes en ppm de CaCO3, según la clasificación habitual.
_HARDNESS_BANDS: tuple[tuple[float, WaterHardness], ...] = (
    (60.0, WaterHardness.SOFT),
    (120.0, WaterHardness.MODERATELY_HARD),
    (180.0, WaterHardness.HARD),
    (float("inf"), WaterHardness.VERY_HARD),
)


def classify_hardness(ppm: float) -> WaterHardness:
    for ceiling, band in _HARDNESS_BANDS:
        if ppm < ceiling:
            return band
    return WaterHardness.VERY_HARD


@dataclass(frozen=True)
class WaterAssessment:
    hardness: WaterHardness
    ppm: float
    estimated: bool
    """True cuando el valor viene de datos regionales, no de una medición."""
    needs_chelation: bool
    explanation: Explanation

    def as_dict(self) -> dict[str, object]:
        return {
            "hardness": self.hardness.value,
            "ppm": round(self.ppm, 1),
            "estimated": self.estimated,
            "needs_chelation": self.needs_chelation,
            "explanation": self.explanation.as_dict(),
        }


def assess_water(
    *,
    measured_ppm: float | None = None,
    regional_ppm: float | None = None,
    reports_limescale: bool | None = None,
    soap_lathers_poorly: bool | None = None,
) -> WaterAssessment | None:
    """Estima la dureza del agua a partir de lo que haya disponible.

    Devuelve `None` cuando no hay ninguna señal: no se inventa un valor
    regional por defecto sólo para poder mostrar algo.
    """
    if measured_ppm is not None:
        ppm, estimated, confidence = measured_ppm, False, 0.95
    elif regional_ppm is not None:
        ppm, estimated, confidence = regional_ppm, True, 0.6
    else:
        signals = [s for s in (reports_limescale, soap_lathers_poorly) if s is not None]
        if not signals:
            return None
        # Dos señales indirectas: se estima el punto medio de la banda "dura",
        # con confianza baja y declarada.
        ppm = 200.0 if all(signals) else 120.0
        estimated, confidence = True, 0.35 if all(signals) else 0.25

    hardness = classify_hardness(ppm)
    uncertainty = ["uncertainty.water_estimated_not_measured"] if estimated else []

    explanation = Explanation(
        summary_key="water.assessment.why",
        inputs_used=("input.water_signals",),
        observations=(f"ppm={ppm:.0f}", f"hardness={hardness.value}"),
        evidence_level="scientific_evidence",
        evidence_confidence=0.90 * confidence,
        personal_confidence=0.0,
        sample_size=0,
        uncertainty_keys=tuple(uncertainty),
        alternatives=("water.alternative.measure_with_test_strip",) if estimated else (),
        params={"clarifying_is_not_chelating": True},
    )

    return WaterAssessment(
        hardness=hardness,
        ppm=ppm,
        estimated=estimated,
        needs_chelation=hardness in {WaterHardness.HARD, WaterHardness.VERY_HARD},
        explanation=explanation,
    )
