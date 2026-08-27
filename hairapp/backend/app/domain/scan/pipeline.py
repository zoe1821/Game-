"""Pipeline del scanner (A3) — con los mocks declarados como tales.

Regla crítica del proyecto: **no fingir que un modelo de visión existe si no
existe.** Aquí eso significa que `MockSegmenter` devuelve `Unavailable`, no una
máscara inventada, y que las etapas que dependen de ella se saltan de forma
visible en vez de producir números plausibles.

Etapas:
  quality_validation -> segmentation -> zone_mapping -> feature_extraction ->
  interpretation -> confidence_calibration -> user_confirmation -> profile_update

Ver docs/07-SCANNER-PIPELINE.md para el estado real de cada una.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import numpy as np

from ..common import Explanation, Measured, Source, Unavailable, clamp
from ..confidence.engine import photo_quality_penalty
from ..hair.attributes import CurlPattern, pattern_from_curl_diameter
from ..hair.zones import ANGLE_COVERAGE, PhotoAngle, Zone, coverage_for
from .quality import PhotoQualityReport, ScanQualityReport, assess_photo


class StageStatus(enum.Enum):
    OK = "ok"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    """La etapa no se pudo ejecutar. Se declara; no se sustituye por un valor."""


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: StageStatus
    reason_key: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "reason_key": self.reason_key,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ScanPhoto:
    angle: PhotoAngle
    image: np.ndarray
    """HxW o HxWx3, valores 0-255."""
    taken_when_wet: bool = False


# --------------------------------------------------------------------------
# Etapa 2: segmentación
# --------------------------------------------------------------------------


class Segmenter(Protocol):
    """Interfaz de segmentación de cabello.

    Está definida para que un modelo real se pueda enchufar sin tocar el resto
    del pipeline. Hoy la única implementación es un mock que devuelve
    `Unavailable`.
    """

    @property
    def is_real_model(self) -> bool: ...

    def segment(self, photo: ScanPhoto) -> np.ndarray | Unavailable: ...


class MockSegmenter:
    """**MOCK DECLARADO.** No hay modelo de segmentación en este repositorio.

    Devuelve `Unavailable` siempre. No devuelve una máscara aproximada, ni una
    elipse centrada, ni nada que se le parezca: cualquiera de esas cosas
    produciría métricas de imagen falsas aguas abajo, y el sistema las
    presentaría como observaciones reales.

    Sustituir por un modelo entrenado (por ejemplo una U-Net de segmentación de
    cabello) implementando `Segmenter`. Nada más del pipeline cambia.
    """

    @property
    def is_real_model(self) -> bool:
        return False

    def segment(self, photo: ScanPhoto) -> np.ndarray | Unavailable:
        return Unavailable(
            reason_key="scan.segmentation.no_model",
            detail=(
                "No hay modelo de segmentación de cabello disponible. Las métricas "
                "de imagen no se calculan y el análisis se basa solo en las "
                "respuestas de la persona usuaria."
            ),
        )


# --------------------------------------------------------------------------
# Etapa 4: extracción de características — REAL cuando hay máscara
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ImageFeatures:
    """Métricas medidas sobre píxeles. Todas reales, ninguna estimada."""

    curl_diameter_mm: float | None = None
    curve_frequency_per_cm: float | None = None
    frizz_index: float | None = None
    uniformity: float | None = None
    definition: float | None = None
    clumping: float | None = None

    @property
    def has_any(self) -> bool:
        return any(v is not None for v in vars(self).values())


def extract_features(
    image: np.ndarray, mask: np.ndarray, *, pixels_per_cm: float | None = None
) -> ImageFeatures:
    """Extrae métricas reales de la región enmascarada.

    Sin `pixels_per_cm` (que requiere una referencia de escala en la foto) las
    medidas absolutas no se pueden calcular. Se devuelven `None`, no una
    conversión inventada: un rizo de 40 píxeles puede ser de 2 mm o de 2 cm
    según la distancia de la cámara.
    """
    if mask.shape != image.shape[:2]:
        raise ValueError("la máscara debe tener la misma forma espacial que la imagen")

    gray = image if image.ndim == 2 else (
        0.299 * image[..., 0] + 0.587 * image[..., 1] + 0.114 * image[..., 2]
    )
    gray = gray.astype(np.float64)
    inside = mask > 0
    if inside.sum() < 100:
        return ImageFeatures()

    # Frecuencia de curva: autocorrelación sobre perfiles horizontales dentro
    # de la máscara. El primer pico secundario da el periodo dominante.
    period_px = _dominant_period(gray, inside)
    frequency = None
    diameter_mm = None
    if period_px is not None and pixels_per_cm:
        frequency = pixels_per_cm / period_px
        # El diámetro del rizo es aproximadamente el periodo de la onda.
        diameter_mm = period_px / pixels_per_cm * 10.0

    # Frizz: energía de bordes en el borde exterior de la máscara. Las hebras
    # que se salen del cuerpo principal son literalmente eso.
    frizz = _frizz_index(gray, inside)

    # Definición: contraste local dentro de la máscara. Un rizo definido tiene
    # sombras marcadas entre grupos; uno difuso no.
    definition = clamp(float(np.std(gray[inside])) / 60.0)

    # Uniformidad: dispersión de los periodos por franja.
    uniformity = _uniformity(gray, inside)

    return ImageFeatures(
        curl_diameter_mm=diameter_mm,
        curve_frequency_per_cm=frequency,
        frizz_index=frizz,
        uniformity=uniformity,
        definition=definition,
        clumping=uniformity,
    )


def _dominant_period(gray: np.ndarray, inside: np.ndarray) -> float | None:
    rows = np.where(inside.any(axis=1))[0]
    if len(rows) < 10:
        return None
    periods: list[float] = []
    for row in rows[:: max(1, len(rows) // 20)]:
        columns = np.where(inside[row])[0]
        if len(columns) < 40:
            continue
        profile = gray[row, columns[0] : columns[-1] + 1]
        profile = profile - profile.mean()
        if np.allclose(profile, 0):
            continue
        correlation = np.correlate(profile, profile, mode="full")[len(profile) - 1 :]
        if correlation[0] == 0:
            continue
        correlation = correlation / correlation[0]
        peak = _first_secondary_peak(correlation)
        if peak is not None:
            periods.append(float(peak))
    if not periods:
        return None
    return float(np.median(periods))


def _first_secondary_peak(correlation: np.ndarray) -> int | None:
    descending = False
    for index in range(1, len(correlation) - 1):
        if not descending:
            if correlation[index] < correlation[index - 1]:
                descending = True
            continue
        if correlation[index] > correlation[index - 1] and correlation[index] >= correlation[index + 1]:
            return index
    return None


def _frizz_index(gray: np.ndarray, inside: np.ndarray) -> float:
    eroded = _erode(inside)
    border = inside & ~eroded
    if border.sum() < 20 or eroded.sum() < 20:
        return 0.0
    gradient_y, gradient_x = np.gradient(gray)
    magnitude = np.hypot(gradient_x, gradient_y)
    border_energy = float(magnitude[border].mean())
    core_energy = float(magnitude[eroded].mean())
    if core_energy == 0:
        return 0.0
    return clamp(border_energy / (core_energy * 3.0))


def _erode(mask: np.ndarray, iterations: int = 3) -> np.ndarray:
    eroded = mask.copy()
    for _ in range(iterations):
        shifted = (
            np.roll(eroded, 1, 0)
            & np.roll(eroded, -1, 0)
            & np.roll(eroded, 1, 1)
            & np.roll(eroded, -1, 1)
        )
        eroded = eroded & shifted
    return eroded


def _uniformity(gray: np.ndarray, inside: np.ndarray) -> float:
    rows = np.where(inside.any(axis=1))[0]
    if len(rows) < 20:
        return 0.0
    bands = np.array_split(rows, 4)
    stds = []
    for band in bands:
        if len(band) == 0:
            continue
        region = gray[band][inside[band]]
        if region.size > 10:
            stds.append(float(np.std(region)))
    if len(stds) < 2:
        return 0.0
    mean_std = float(np.mean(stds))
    if mean_std == 0:
        return 1.0
    return clamp(1.0 - float(np.std(stds)) / mean_std)


# --------------------------------------------------------------------------
# Pipeline completo
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ZoneObservation:
    """Lo observado en una zona. Puede estar vacío, y eso se dice."""

    zone: Zone
    observed: bool
    features: ImageFeatures | None = None
    source_angles: tuple[PhotoAngle, ...] = ()
    quality_score: float = 0.0
    not_observed_reason_key: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "zone": self.zone.value,
            "observed": self.observed,
            "source_angles": [a.value for a in self.source_angles],
            "quality_score": round(self.quality_score, 3),
            "not_observed_reason_key": self.not_observed_reason_key,
            "features": (
                {k: (round(v, 3) if isinstance(v, float) else v) for k, v in vars(self.features).items()}
                if self.features
                else None
            ),
        }


@dataclass(frozen=True)
class ScanResult:
    quality: ScanQualityReport
    stages: tuple[StageResult, ...]
    observations: tuple[ZoneObservation, ...]
    estimates: dict[Zone, dict[str, Measured[object]]]
    requires_user_confirmation: bool
    explanation: Explanation

    @property
    def used_image_analysis(self) -> bool:
        return any(o.observed and o.features and o.features.has_any for o in self.observations)

    def as_dict(self) -> dict[str, object]:
        return {
            "quality": self.quality.as_dict(),
            "stages": [s.as_dict() for s in self.stages],
            "observations": [o.as_dict() for o in self.observations],
            "used_image_analysis": self.used_image_analysis,
            "requires_user_confirmation": self.requires_user_confirmation,
            "estimates": {
                zone.value: {
                    field: {
                        "value": _plain(m.value),
                        "confidence": round(m.confidence, 3),
                        "source": m.source.value,
                    }
                    for field, m in fields.items()
                }
                for zone, fields in self.estimates.items()
            },
            "explanation": self.explanation.as_dict(),
        }


def _plain(value: object) -> object:
    return value.value if isinstance(value, enum.Enum) else value


class ScanPipeline:
    def __init__(self, segmenter: Segmenter | None = None) -> None:
        self._segmenter = segmenter or MockSegmenter()

    def run(
        self,
        photos: Sequence[ScanPhoto],
        *,
        pixels_per_cm: float | None = None,
        today: date | None = None,
    ) -> ScanResult:
        stages: list[StageResult] = []

        # 1. Validación de calidad — REAL
        reports = [assess_photo(p.image, p.angle) for p in photos]
        quality = ScanQualityReport(photos=tuple(reports))
        stages.append(StageResult("quality_validation", StageStatus.OK))

        usable = [
            (photo, report)
            for photo, report in zip(photos, reports, strict=True)
            if report.is_usable
        ]

        # 2. Segmentación — MOCK declarado hoy
        masks: dict[PhotoAngle, np.ndarray] = {}
        segmentation_reason: str | None = None
        for photo, _ in usable:
            outcome = self._segmenter.segment(photo)
            if isinstance(outcome, Unavailable):
                segmentation_reason = outcome.reason_key
                continue
            masks[photo.angle] = outcome

        if not masks:
            stages.append(
                StageResult(
                    "segmentation",
                    StageStatus.UNAVAILABLE,
                    reason_key=segmentation_reason or "scan.segmentation.no_model",
                    detail="Sin máscara de cabello no se calculan métricas de imagen.",
                )
            )
            stages.append(
                StageResult("zone_mapping", StageStatus.SKIPPED, "scan.skipped.no_mask")
            )
            stages.append(
                StageResult("feature_extraction", StageStatus.SKIPPED, "scan.skipped.no_mask")
            )
        else:
            stages.append(StageResult("segmentation", StageStatus.OK))
            stages.append(StageResult("zone_mapping", StageStatus.OK))
            stages.append(StageResult("feature_extraction", StageStatus.OK))

        # 3-4. Mapeo a zonas y extracción
        observations = self._observe(usable, masks, pixels_per_cm)

        # 5-6. Interpretación y calibración de confianza
        estimates = self._interpret(observations, today)
        stages.append(StageResult("interpretation", StageStatus.OK))
        stages.append(StageResult("confidence_calibration", StageStatus.OK))

        # 7. Confirmación: siempre obligatoria (A3/A1.4)
        stages.append(
            StageResult(
                "user_confirmation",
                StageStatus.OK,
                reason_key="scan.confirmation.required",
            )
        )

        uncertainty = ["uncertainty.estimates_need_confirmation"]
        if not masks:
            uncertainty.append("uncertainty.no_image_analysis")
        if quality.angles_to_retake:
            uncertainty.append("uncertainty.some_photos_unusable")
        if quality.missing_required_angles:
            uncertainty.append("uncertainty.missing_angles")

        explanation = Explanation(
            summary_key="scan.result.why",
            inputs_used=("input.photos", "input.photo_quality"),
            observations=tuple(
                f"{o.zone.value}:{'observada' if o.observed else 'no observada'}"
                for o in observations
            ),
            evidence_level="professional_consensus",
            evidence_confidence=0.70,
            personal_confidence=0.0,
            sample_size=0,
            uncertainty_keys=tuple(uncertainty),
            params={
                "segmentation_is_mock": not self._segmenter.is_real_model,
                "mean_photo_quality": round(quality.mean_score, 3),
            },
        )

        return ScanResult(
            quality=quality,
            stages=tuple(stages),
            observations=tuple(observations),
            estimates=estimates,
            requires_user_confirmation=True,
            explanation=explanation,
        )

    def _observe(
        self,
        usable: Sequence[tuple[ScanPhoto, PhotoQualityReport]],
        masks: dict[PhotoAngle, np.ndarray],
        pixels_per_cm: float | None,
    ) -> list[ZoneObservation]:
        angles = [photo.angle for photo, _ in usable]
        coverage = coverage_for(angles)
        quality_by_angle = {photo.angle: report.score for photo, report in usable}
        image_by_angle = {photo.angle: photo.image for photo, _ in usable}

        observations: list[ZoneObservation] = []
        for zone in Zone:
            source_angles = tuple(
                angle for angle in angles if zone in ANGLE_COVERAGE.get(angle, ())
            )
            if zone in coverage.uncovered or not source_angles:
                observations.append(
                    ZoneObservation(
                        zone=zone,
                        observed=False,
                        not_observed_reason_key="scan.zone.not_photographed",
                    )
                )
                continue

            best_angle = max(source_angles, key=lambda a: quality_by_angle.get(a, 0.0))
            mask = masks.get(best_angle)
            features = None
            if mask is not None:
                features = extract_features(
                    image_by_angle[best_angle], mask, pixels_per_cm=pixels_per_cm
                )
            observations.append(
                ZoneObservation(
                    zone=zone,
                    observed=True,
                    features=features,
                    source_angles=source_angles,
                    quality_score=quality_by_angle.get(best_angle, 0.0),
                    not_observed_reason_key=(
                        None if features and features.has_any else "scan.zone.no_image_metrics"
                    ),
                )
            )
        return observations

    def _interpret(
        self, observations: Sequence[ZoneObservation], today: date | None
    ) -> dict[Zone, dict[str, Measured[object]]]:
        """Convierte métricas en estimaciones con confianza calibrada.

        Solo produce estimaciones **de lo que se midió**. Una zona sin métricas
        no aparece aquí: el resto del perfil se completa con las respuestas de
        la persona, y la app lo dice.
        """
        estimates: dict[Zone, dict[str, Measured[object]]] = {}
        for observation in observations:
            if not observation.observed or not observation.features:
                continue
            features = observation.features
            fields: dict[str, Measured[object]] = {}
            penalty = photo_quality_penalty(observation.quality_score)

            if features.curl_diameter_mm is not None:
                pattern: CurlPattern = pattern_from_curl_diameter(features.curl_diameter_mm)
                fields["pattern"] = Measured(
                    value=pattern,
                    source=Source.AI_VISION,
                    confidence=min(0.65 * penalty, Source.AI_VISION.confidence_ceiling),
                    observed_at=today,
                )
                fields["curl_diameter_mm"] = Measured(
                    value=features.curl_diameter_mm,
                    source=Source.AI_VISION,
                    confidence=min(0.60 * penalty, Source.AI_VISION.confidence_ceiling),
                    observed_at=today,
                )
            if features.frizz_index is not None:
                fields["frizz_level"] = Measured(
                    value=features.frizz_index,
                    source=Source.AI_VISION,
                    confidence=min(0.55 * penalty, Source.AI_VISION.confidence_ceiling),
                    observed_at=today,
                )
            if features.definition is not None:
                fields["definition_level"] = Measured(
                    value=features.definition,
                    source=Source.AI_VISION,
                    confidence=min(0.50 * penalty, Source.AI_VISION.confidence_ceiling),
                    observed_at=today,
                )
            if fields:
                estimates[observation.zone] = fields
        return estimates
