"""Crecimiento y retención de longitud (A13).

**La distinción que este módulo existe para hacer.** Crecimiento y retención de
longitud no son lo mismo, y confundirlos es el error más extendido en el
cuidado capilar:

  - El **crecimiento** ocurre en el folículo, bajo la piel. Su velocidad es
    bastante estable por persona y no la cambia ningún producto tópico.
  - La **retención** es cuánta de esa longitud se conserva en las puntas en vez
    de perderse por rotura. Es lo único sobre lo que se puede actuar.

Alguien cuyo cabello "no crece" casi siempre tiene un problema de retención:
crece por arriba a la misma velocidad de siempre y se rompe por abajo al mismo
ritmo. Decirle que su cabello no crece es falso y además desmoralizante.

Por eso este módulo mide las dos cosas por separado y nunca reporta una sola
cifra de "crecimiento".

**La limitación que hay que decir en voz alta.** Medir la longitud de las
puntas a lo largo del tiempo **no basta** para separar las dos cosas. Si
alguien gana 1 cm en seis meses, eso es compatible con dos historias
completamente distintas:

  - crece 0,17 cm/mes y no se rompe nada, o
  - crece 1,25 cm/mes y se rompen 6,5 cm.

Son indistinguibles con ese único dato. Así que aquí el crecimiento **se
asume** del rango poblacional y se declara como supuesto, salvo que exista una
medición real de raíz — que sí es posible: en cabello teñido, la distancia
desde el cuero cabelludo hasta la línea de color es crecimiento medido, no
estimado. Cuando existe ese dato, se usa y la confianza sube.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date

from ..common import Explanation, clamp

#: Rango de crecimiento del cuero cabelludo humano, en cm/mes. Es un rango
#: poblacional amplio: hay variación individual real, y la media que se cita
#: (~1,25 cm/mes) es solo eso, una media.
TYPICAL_GROWTH_CM_PER_MONTH = (0.8, 1.5)
TYPICAL_GROWTH_MIDPOINT = 1.25


@dataclass(frozen=True)
class LengthObservation:
    """Una medición de longitud en una fecha."""

    observed_on: date
    length_cm: float
    #: Si se cortó entre esta medición y la anterior, cuánto.
    trimmed_cm: float = 0.0
    #: Crecimiento medido en la raíz: distancia del cuero cabelludo a la línea
    #: de color en cabello teñido. Es la única forma casera de **medir** el
    #: crecimiento en vez de suponerlo.
    root_regrowth_cm: float | None = None


class GrowthSource(enum.Enum):
    MEASURED_AT_ROOT = "measured_at_root"
    """Medido de verdad, con la línea de color como referencia."""
    ASSUMED_POPULATION = "assumed_population"
    """Supuesto del rango poblacional. La longitud sola no puede medirlo."""


@dataclass(frozen=True)
class GrowthReading:
    """Lectura del periodo, con las dos cifras separadas y su procedencia."""

    months: float
    observed_gain_cm: float
    """Lo que ha cambiado la longitud medida. Puede ser negativo."""
    trimmed_cm: float
    growth_cm_per_month: float
    growth_source: GrowthSource
    total_growth_cm: float
    retention_ratio: float
    """De lo que creció, qué fracción sigue puesta. 1.0 = no se perdió nada."""
    lost_to_breakage_cm: float
    growth_is_typical: bool
    sample_size: int
    explanation: Explanation

    @property
    def is_retention_problem(self) -> bool:
        """Se pierde una parte apreciable de lo que crece."""
        return self.retention_ratio < 0.6

    @property
    def growth_is_measured(self) -> bool:
        return self.growth_source is GrowthSource.MEASURED_AT_ROOT

    def as_dict(self) -> dict[str, object]:
        return {
            "months": round(self.months, 2),
            "observed_gain_cm": round(self.observed_gain_cm, 2),
            "trimmed_cm": round(self.trimmed_cm, 2),
            "growth_cm_per_month": round(self.growth_cm_per_month, 3),
            "growth_source": self.growth_source.value,
            "growth_is_measured": self.growth_is_measured,
            "total_growth_cm": round(self.total_growth_cm, 2),
            "retention_ratio": round(self.retention_ratio, 3),
            "lost_to_breakage_cm": round(self.lost_to_breakage_cm, 2),
            "growth_is_typical": self.growth_is_typical,
            "is_retention_problem": self.is_retention_problem,
            "sample_size": self.sample_size,
            "explanation": self.explanation.as_dict(),
        }


#: Mínimo de meses para decir algo. Por debajo, la diferencia entre dos
#: mediciones caseras es sobre todo error de medición.
MIN_MONTHS_FOR_A_READING = 2.0


def read_growth(observations: list[LengthObservation]) -> GrowthReading | None:
    """Lee el periodo. Devuelve `None` si no hay datos suficientes.

    Esa negativa es la respuesta correcta: con dos mediciones separadas por tres
    semanas, la diferencia es ruido de cómo se estiró el pelo al medir.
    """
    if len(observations) < 2:
        return None

    ordered = sorted(observations, key=lambda o: o.observed_on)
    first, last = ordered[0], ordered[-1]
    months = (last.observed_on - first.observed_on).days / 30.44
    if months < MIN_MONTHS_FOR_A_READING:
        return None

    trimmed = sum(o.trimmed_cm for o in ordered[1:])
    observed_gain = last.length_cm - first.length_cm

    # El crecimiento se mide si hay línea de color; si no, se supone.
    root_measurements = [o.root_regrowth_cm for o in ordered if o.root_regrowth_cm is not None]
    if root_measurements:
        per_month = max(root_measurements) / months if months else 0.0
        source = GrowthSource.MEASURED_AT_ROOT
    else:
        per_month = TYPICAL_GROWTH_MIDPOINT
        source = GrowthSource.ASSUMED_POPULATION

    total_growth = per_month * months

    # Lo que se conserva es lo que se ve más lo que se cortó a propósito:
    # cortar es una decisión, no una rotura.
    kept = observed_gain + trimmed
    retention = clamp(kept / total_growth) if total_growth > 0 else 0.0
    lost = max(0.0, total_growth - kept)

    low, high = TYPICAL_GROWTH_CM_PER_MONTH
    is_typical = low <= per_month <= high

    uncertainty = ["uncertainty.home_measurement"]
    if source is GrowthSource.ASSUMED_POPULATION:
        # Lo más importante que decir de esta lectura.
        uncertainty.append("uncertainty.growth_rate_assumed_not_measured")
    if len(ordered) == 2:
        uncertainty.append("uncertainty.only_two_measurements")
    if months < 4:
        uncertainty.append("uncertainty.short_period")

    explanation = Explanation(
        summary_key="growth.reading.why",
        inputs_used=("input.length_measurements", "input.trims")
        + (("input.root_regrowth",) if root_measurements else ()),
        observations=(
            f"months={months:.1f}",
            f"observed_gain_cm={observed_gain:.1f}",
            f"trimmed_cm={trimmed:.1f}",
            f"growth_source={source.value}",
        ),
        evidence_level="scientific_evidence",
        evidence_confidence=0.90 if root_measurements else 0.55,
        personal_confidence=clamp(len(ordered) / 6.0) * clamp(months / 6.0),
        sample_size=len(ordered),
        uncertainty_keys=tuple(uncertainty),
        alternatives=(
            ("growth.alternative.measure_same_way_each_time",)
            if root_measurements
            else (
                "growth.alternative.measure_root_regrowth",
                "growth.alternative.measure_same_way_each_time",
            )
        ),
        params={
            "typical_range_cm_per_month": list(TYPICAL_GROWTH_CM_PER_MONTH),
            "growth_is_not_retention": True,
        },
    )

    return GrowthReading(
        months=months,
        observed_gain_cm=observed_gain,
        trimmed_cm=trimmed,
        growth_cm_per_month=per_month,
        growth_source=source,
        total_growth_cm=total_growth,
        retention_ratio=retention,
        lost_to_breakage_cm=lost,
        growth_is_typical=is_typical,
        sample_size=len(ordered),
        explanation=explanation,
    )


def expected_length(
    starting_cm: float, months: float, *, cm_per_month: float | None = None
) -> tuple[float, float]:
    """Rango de longitud esperable si no se pierde nada por rotura.

    Devuelve un rango, no una cifra: la velocidad de crecimiento varía entre
    personas y dar un número exacto sería falsa precisión.
    """
    if cm_per_month is not None:
        return (starting_cm + cm_per_month * months, starting_cm + cm_per_month * months)
    low, high = TYPICAL_GROWTH_CM_PER_MONTH
    return (starting_cm + low * months, starting_cm + high * months)
