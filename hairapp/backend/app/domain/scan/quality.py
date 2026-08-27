"""Validación de calidad de foto — implementación REAL (etapa 1 del pipeline).

Corre sobre los píxeles de verdad: varianza del Laplaciano para el desenfoque,
histograma para la exposición, y cobertura para el encuadre. Nada aquí es un
mock.

Diseñada para ejecutarse también en el dispositivo antes de subir: la persona
descubre que la foto salió movida en el momento, no cinco minutos después.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from ..common import clamp
from ..hair.zones import PhotoAngle


class QualityIssue(enum.Enum):
    TOO_BLURRY = "too_blurry"
    UNDEREXPOSED = "underexposed"
    OVEREXPOSED = "overexposed"
    LOW_RESOLUTION = "low_resolution"
    LOW_CONTRAST = "low_contrast"
    POSSIBLE_FILTER = "possible_filter"
    SUBJECT_TOO_SMALL = "subject_too_small"

    @property
    def message_key(self) -> str:
        return f"scan.quality.{self.value}"

    @property
    def is_blocking(self) -> bool:
        """Bloqueante = hay que repetir la foto. Los avisos no bloquean."""
        return self in _BLOCKING


_BLOCKING = frozenset(
    {
        QualityIssue.TOO_BLURRY,
        QualityIssue.UNDEREXPOSED,
        QualityIssue.OVEREXPOSED,
        QualityIssue.LOW_RESOLUTION,
    }
)


# ---------------------------------------------------------------------------
# UMBRALES — estado de calibración
#
# Calibrados contra un conjunto real de 35 fotos (cabello rizado y texturizado
# en distintas condiciones, más fotos de etiquetas de producto), no contra
# imágenes sintéticas.
#
# Lo que ese conjunto reveló y aquí está corregido: la varianza del Laplaciano
# **no es invariante a la escala**. La misma foto medía 1948 a 720 px y 167 a
# 2048 px, un factor de doce. La versión anterior intentaba compensarlo
# multiplicando por la raíz del cociente de lados, lo que empeoraba el
# problema, y acababa rechazando por "movida" toda foto de cámara moderna.
#
# La corrección es medir siempre a una resolución de trabajo fija
# (`BLUR_WORKING_SIDE_PX`): así el número significa lo mismo venga de donde
# venga la foto.
#
# Lo que el conjunto **no** mostró, y conviene dejar escrito para no repetir la
# sospecha: no hay sesgo por luminancia. A igual resolución, la correlación
# entre brillo medio y la métrica fue +0.01. El cabello oscuro no se penaliza.
#
# `score` sigue siendo continuo y alimenta la penalización de confianza: una
# foto justa produce una estimación menos confiada, no un rechazo ni una
# estimación falsamente segura.
# ---------------------------------------------------------------------------

#: Resolución a la que se mide el desenfoque. Fija a propósito: es lo que hace
#: la métrica comparable entre una foto de 720 px y una de 4032 px.
BLUR_WORKING_SIDE_PX = 720

#: Rejilla en la que se divide el encuadre para medir nitidez por regiones.
_TILE_GRID = 6

#: Percentil de celdas que se toma como "lo más nítido del encuadre". No es el
#: máximo: una sola celda con un reflejo o un borde duro no debe decidir por
#: toda la foto.
_SHARPEST_PERCENTILE = 90

MIN_SHORT_SIDE_PX = 720
BLUR_VARIANCE_THRESHOLD = 300.0
CLIPPED_HIGHLIGHT_RATIO = 0.12
CLIPPED_SHADOW_RATIO = 0.25
MIN_CONTRAST_STD = 25.0
SATURATION_ANOMALY_THRESHOLD = 0.78


@dataclass(frozen=True)
class PhotoQualityReport:
    angle: PhotoAngle
    score: float
    """0-1. Alimenta la penalización de confianza del análisis."""
    issues: tuple[QualityIssue, ...]
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def must_retake(self) -> bool:
        return any(issue.is_blocking for issue in self.issues)

    @property
    def is_usable(self) -> bool:
        return not self.must_retake

    def as_dict(self) -> dict[str, object]:
        return {
            "angle": self.angle.value,
            "score": round(self.score, 3),
            "must_retake": self.must_retake,
            "issues": [
                {"code": i.value, "message_key": i.message_key, "blocking": i.is_blocking}
                for i in self.issues
            ],
            "metrics": {k: round(v, 3) for k, v in self.metrics.items()},
        }


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float64)
    # Luminancia perceptual (Rec. 601): el verde pesa más porque el ojo lo ve más.
    return (
        0.299 * image[..., 0] + 0.587 * image[..., 1] + 0.114 * image[..., 2]
    ).astype(np.float64)


def _resize_nearest(gray: np.ndarray, target_short_side: int) -> np.ndarray:
    """Reescala por muestreo, sin dependencias de imagen en el dominio.

    Basta para medir nitidez: lo que importa es llevar todas las fotos a la
    misma densidad de detalle antes de comparar, no la calidad del reescalado.
    """
    height, width = gray.shape
    short_side = min(height, width)
    if short_side <= target_short_side:
        return gray
    factor = target_short_side / short_side
    rows = (np.arange(int(height * factor)) / factor).astype(np.int64)
    cols = (np.arange(int(width * factor)) / factor).astype(np.int64)
    return gray[np.clip(rows, 0, height - 1)][:, np.clip(cols, 0, width - 1)]


def sharpness(gray: np.ndarray) -> float:
    """Nitidez de la parte más nítida del encuadre, a resolución fija.

    Dos correcciones sobre la varianza del Laplaciano a secas, ambas salidas de
    mirar fotos reales:

    1. **Resolución fija.** Sin ella la misma foto medía 1948 a 720 px y 167 a
       2048 px.

    2. **Por regiones, no global.** Una foto bien compuesta de cabello tiene
       mucho fondo liso: una camiseta de color plano, una pared, un armario.
       Todo eso es superficie sin detalle que hunde la varianza global y hacía
       que fotos perfectamente nítidas se rechazaran por "movidas". Lo mismo
       ocurría con los primeros planos de etiquetas, donde el fondo sale
       desenfocado a propósito.

       Se divide el encuadre en celdas y se toma un percentil alto. La pregunta
       que responde es la correcta: *¿hay alguna parte de esta foto que esté
       enfocada?* Si el cabello está nítido, la foto sirve, por mucho fondo
       plano que la rodee.
    """
    working = _resize_nearest(gray, BLUR_WORKING_SIDE_PX)
    height, width = working.shape
    if min(height, width) < _TILE_GRID * 4:
        return laplacian_variance(working)

    tile_h, tile_w = height // _TILE_GRID, width // _TILE_GRID
    variances = [
        laplacian_variance(
            working[row * tile_h : (row + 1) * tile_h, col * tile_w : (col + 1) * tile_w]
        )
        for row in range(_TILE_GRID)
        for col in range(_TILE_GRID)
    ]
    return float(np.percentile(variances, _SHARPEST_PERCENTILE))


def laplacian_variance(gray: np.ndarray) -> float:
    """Varianza de la respuesta del Laplaciano: la medida estándar de nitidez.

    Una imagen enfocada tiene bordes marcados, que producen una respuesta amplia
    y dispersa; una movida los suaviza y la varianza se hunde.

    Es sensible a la escala: para comparar fotos de distinto tamaño hay que
    usar `sharpness()`, que mide a una resolución fija.
    """
    kernel = np.array([[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]])
    padded = np.pad(gray, 1, mode="edge")
    response = np.zeros_like(gray)
    for dy in range(3):
        for dx in range(3):
            weight = kernel[dy, dx]
            if weight != 0.0:
                response += weight * padded[dy : dy + gray.shape[0], dx : dx + gray.shape[1]]
    return float(np.var(response))


def saturation_ratio(image: np.ndarray) -> float:
    """Saturación media en HSV, aproximada sin convertir todo el espacio.

    Se usa solo como heurística de "esto parece llevar filtro". Es una
    heurística y se declara como tal: nunca bloquea, solo avisa.
    """
    if image.ndim != 3 or image.shape[2] < 3:
        return 0.0
    rgb = image[..., :3].astype(np.float64)
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        saturation = np.where(maximum > 0, (maximum - minimum) / maximum, 0.0)
    return float(np.nanmean(saturation))


def assess_photo(
    image: np.ndarray,
    angle: PhotoAngle,
    *,
    subject_mask: np.ndarray | None = None,
) -> PhotoQualityReport:
    """Evalúa una foto. `image` es un array HxW o HxWx3 con valores 0-255.

    `subject_mask` es opcional: cuando existe se comprueba también el encuadre.
    Cuando no, no se inventa: simplemente no se evalúa ese aspecto.
    """
    if image.ndim not in (2, 3):
        raise ValueError("se espera una imagen HxW o HxWx3")

    gray = _to_grayscale(image)
    height, width = gray.shape
    short_side = min(height, width)

    issues: list[QualityIssue] = []
    metrics: dict[str, float] = {}

    metrics["short_side_px"] = float(short_side)
    if short_side < MIN_SHORT_SIDE_PX:
        issues.append(QualityIssue.LOW_RESOLUTION)

    measured_sharpness = sharpness(gray)
    metrics["laplacian_variance"] = laplacian_variance(gray)
    metrics["sharpness"] = measured_sharpness
    if measured_sharpness < BLUR_VARIANCE_THRESHOLD:
        issues.append(QualityIssue.TOO_BLURRY)

    highlights = float(np.mean(gray >= 250))
    shadows = float(np.mean(gray <= 8))
    metrics["clipped_highlights"] = highlights
    metrics["clipped_shadows"] = shadows
    if highlights > CLIPPED_HIGHLIGHT_RATIO:
        issues.append(QualityIssue.OVEREXPOSED)
    if shadows > CLIPPED_SHADOW_RATIO:
        issues.append(QualityIssue.UNDEREXPOSED)

    contrast = float(np.std(gray))
    metrics["contrast_std"] = contrast
    if contrast < MIN_CONTRAST_STD:
        issues.append(QualityIssue.LOW_CONTRAST)

    saturation = saturation_ratio(image)
    metrics["mean_saturation"] = saturation
    if saturation > SATURATION_ANOMALY_THRESHOLD:
        issues.append(QualityIssue.POSSIBLE_FILTER)

    if subject_mask is not None:
        coverage = float(np.mean(subject_mask > 0))
        metrics["subject_coverage"] = coverage
        if coverage < 0.10:
            issues.append(QualityIssue.SUBJECT_TOO_SMALL)

    return PhotoQualityReport(
        angle=angle,
        score=_score(metrics, issues),
        issues=tuple(issues),
        metrics=metrics,
    )


def _score(metrics: dict[str, float], issues: Sequence[QualityIssue]) -> float:
    """Puntuación continua, no un aprobado/suspenso.

    La usa el calibrador de confianza: una foto justa produce una estimación
    menos confiada, no una estimación falsa.
    """
    sharp = clamp(metrics.get("sharpness", 0.0) / (BLUR_VARIANCE_THRESHOLD * 4))
    exposure = clamp(
        1.0
        - metrics.get("clipped_highlights", 0.0) / CLIPPED_HIGHLIGHT_RATIO * 0.5
        - metrics.get("clipped_shadows", 0.0) / CLIPPED_SHADOW_RATIO * 0.5
    )
    contrast = clamp(metrics.get("contrast_std", 0.0) / (MIN_CONTRAST_STD * 2.5))
    resolution = clamp(metrics.get("short_side_px", 0.0) / (MIN_SHORT_SIDE_PX * 1.5))

    score = 0.4 * sharp + 0.25 * exposure + 0.2 * contrast + 0.15 * resolution
    if any(i.is_blocking for i in issues):
        score *= 0.4
    return clamp(score)


@dataclass(frozen=True)
class ScanQualityReport:
    """Calidad del set completo. Pide repetir solo lo que hace falta (A3)."""

    photos: tuple[PhotoQualityReport, ...]

    @property
    def angles_to_retake(self) -> tuple[PhotoAngle, ...]:
        return tuple(p.angle for p in self.photos if p.must_retake)

    @property
    def usable_photos(self) -> tuple[PhotoQualityReport, ...]:
        return tuple(p for p in self.photos if p.is_usable)

    @property
    def missing_required_angles(self) -> tuple[PhotoAngle, ...]:
        provided = {p.angle for p in self.usable_photos}
        return tuple(a for a in PhotoAngle if a.is_required and a not in provided)

    @property
    def mean_score(self) -> float:
        usable = self.usable_photos
        if not usable:
            return 0.0
        return sum(p.score for p in usable) / len(usable)

    @property
    def is_complete(self) -> bool:
        return not self.angles_to_retake and not self.missing_required_angles

    def as_dict(self) -> dict[str, object]:
        return {
            "photos": [p.as_dict() for p in self.photos],
            "angles_to_retake": [a.value for a in self.angles_to_retake],
            "missing_required_angles": [a.value for a in self.missing_required_angles],
            "mean_score": round(self.mean_score, 3),
            "is_complete": self.is_complete,
        }
