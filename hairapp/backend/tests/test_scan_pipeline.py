import numpy as np
import pytest

from app.domain.common import Source, Unavailable
from app.domain.hair.zones import PhotoAngle, Zone
from app.domain.scan.pipeline import (
    MockSegmenter,
    ScanPhoto,
    ScanPipeline,
    StageStatus,
    extract_features,
)
from app.domain.scan.quality import QualityIssue, assess_photo


def _strand_texture(size: int = 900, seed: int = 3, frequency: float = 1.7) -> np.ndarray:
    """Textura parecida a hebras: lo que el Laplaciano mide en una foto real."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    strands = 40 * np.sin(x * frequency + 8 * np.sin(y / 40.0)) + 18 * rng.standard_normal((size, size))
    base = 120 + 35 * np.sin(y / 120.0) + strands
    return np.clip(np.stack([base, base * 0.94, base * 0.88], -1), 0, 255)


def _blur(image: np.ndarray, iterations: int) -> np.ndarray:
    out = image.astype(np.float64).copy()
    for _ in range(iterations):
        out = (
            np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1) + out
        ) / 5
    return out


# --- validación de calidad: implementación real ---------------------------


def test_blur_detection_responds_to_actual_blur() -> None:
    sharp = assess_photo(_strand_texture(), PhotoAngle.FRONT)
    blurred = assess_photo(_blur(_strand_texture(), 8), PhotoAngle.FRONT)
    assert sharp.metrics["sharpness"] > blurred.metrics["sharpness"]
    assert not sharp.must_retake
    assert QualityIssue.TOO_BLURRY in blurred.issues


def test_sharpness_is_scale_invariant() -> None:
    """Encontrado con fotos reales: la misma foto medía 1948 a 720 px y 167 a
    2048 px, así que el validador rechazaba por "movida" cualquier captura de
    una cámara moderna.

    La textura de prueba usa un periodo de ~7 px, que es el orden en el que se
    ven las hebras a distancia normal de captura. Con periodos cercanos al
    límite de Nyquist el reescalado produce aliasing y la prueba mediría eso en
    vez de la propiedad que interesa.
    """
    from PIL import Image

    grey = Image.fromarray(_strand_texture(1440, frequency=0.9)[..., 0].astype(np.uint8))
    measurements = [
        assess_photo(
            np.stack([np.asarray(grey.resize((side, side), Image.LANCZOS), dtype=np.float64)] * 3, -1),
            PhotoAngle.FRONT,
        ).metrics["sharpness"]
        for side in (2048, 1440, 1080, 800)
    ]
    assert min(measurements) > 0
    # Antes la dispersión superaba 10x; ahora se mantiene acotada.
    assert max(measurements) / min(measurements) < 2.0


def test_flat_background_does_not_make_a_sharp_photo_look_blurry() -> None:
    """Una foto bien compuesta tiene mucho fondo liso (camiseta, pared). Medir
    la varianza global la penalizaba; se mide por regiones."""
    texture = _strand_texture(900)
    framed = np.full_like(texture, 170.0)
    framed[250:650, 250:650] = texture[250:650, 250:650]

    report = assess_photo(framed, PhotoAngle.FRONT)
    assert QualityIssue.TOO_BLURRY not in report.issues


def test_dark_photo_is_rejected() -> None:
    report = assess_photo(np.full((900, 900, 3), 3.0), PhotoAngle.FRONT)
    assert QualityIssue.UNDEREXPOSED in report.issues
    assert report.must_retake


def test_low_resolution_is_rejected() -> None:
    report = assess_photo(_strand_texture(300), PhotoAngle.FRONT)
    assert QualityIssue.LOW_RESOLUTION in report.issues


def test_quality_score_is_continuous_not_pass_fail() -> None:
    scores = [assess_photo(_blur(_strand_texture(), n), PhotoAngle.FRONT).score for n in (0, 5, 9)]
    assert scores[0] > scores[1] > scores[2]


def test_only_bad_photos_are_asked_to_be_retaken() -> None:
    """A3: no se pide repetir el set entero por una foto mala."""
    photos = [
        ScanPhoto(PhotoAngle.FRONT, _strand_texture()),
        ScanPhoto(PhotoAngle.CROWN_TOP, _blur(_strand_texture(), 10)),
        ScanPhoto(PhotoAngle.BACK, _strand_texture()),
        ScanPhoto(PhotoAngle.ENDS_CLOSEUP, _strand_texture()),
        ScanPhoto(PhotoAngle.LEFT_SIDE, _strand_texture()),
    ]
    result = ScanPipeline().run(photos)
    assert result.quality.angles_to_retake == (PhotoAngle.CROWN_TOP,)


# --- el mock se comporta como un mock -------------------------------------


def test_mock_segmenter_returns_unavailable_not_a_fake_mask() -> None:
    """Regla crítica del proyecto: no fingir que el modelo existe."""
    segmenter = MockSegmenter()
    assert not segmenter.is_real_model
    outcome = segmenter.segment(ScanPhoto(PhotoAngle.FRONT, _strand_texture()))
    assert isinstance(outcome, Unavailable)
    assert outcome.reason_key == "scan.segmentation.no_model"


def test_pipeline_declares_the_missing_model_and_produces_no_estimates() -> None:
    photos = [ScanPhoto(a, _strand_texture()) for a in (PhotoAngle.FRONT, PhotoAngle.BACK)]
    result = ScanPipeline().run(photos)

    stages = {s.stage: s for s in result.stages}
    assert stages["segmentation"].status is StageStatus.UNAVAILABLE
    assert stages["zone_mapping"].status is StageStatus.SKIPPED
    assert stages["feature_extraction"].status is StageStatus.SKIPPED

    assert result.estimates == {}
    assert not result.used_image_analysis
    assert "uncertainty.no_image_analysis" in result.explanation.uncertainty_keys
    assert result.explanation.params["segmentation_is_mock"] is True


def test_zones_that_were_not_photographed_are_reported_as_such() -> None:
    photos = [ScanPhoto(PhotoAngle.FRONT, _strand_texture())]
    result = ScanPipeline().run(photos)
    nape = next(o for o in result.observations if o.zone is Zone.NAPE)
    assert not nape.observed
    assert nape.not_observed_reason_key == "scan.zone.not_photographed"


def test_user_confirmation_is_always_required() -> None:
    """A1.4: nada entra al perfil sin que la persona lo confirme o corrija."""
    result = ScanPipeline().run([ScanPhoto(PhotoAngle.FRONT, _strand_texture())])
    assert result.requires_user_confirmation


# --- con un segmentador real, las etapas siguientes sí corren --------------


class _FixedSegmenter:
    """Segmentador de prueba. Existe solo para verificar que la interfaz
    funciona: no pretende ser un modelo."""

    is_real_model = True

    def segment(self, photo: ScanPhoto) -> np.ndarray:
        mask = np.zeros(photo.image.shape[:2], dtype=bool)
        mask[100:800, 100:800] = True
        return mask


def test_real_segmenter_unlocks_the_downstream_stages() -> None:
    photos = [ScanPhoto(a, _strand_texture()) for a in (PhotoAngle.FRONT, PhotoAngle.BACK)]
    result = ScanPipeline(_FixedSegmenter()).run(photos, pixels_per_cm=40.0)

    stages = {s.stage: s.status for s in result.stages}
    assert stages["segmentation"] is StageStatus.OK
    assert stages["feature_extraction"] is StageStatus.OK
    assert result.used_image_analysis
    assert result.estimates


def test_image_estimates_are_marked_as_coming_from_vision_and_are_not_certain() -> None:
    photos = [ScanPhoto(PhotoAngle.FRONT, _strand_texture())]
    result = ScanPipeline(_FixedSegmenter()).run(photos, pixels_per_cm=40.0)
    for fields in result.estimates.values():
        for measured in fields.values():
            assert measured.source is Source.AI_VISION
            assert measured.confidence < 1.0
            assert measured.confidence <= Source.AI_VISION.confidence_ceiling


def test_absolute_measurements_need_a_scale_reference() -> None:
    """Sin escala, un rizo de 40 px puede ser de 2 mm o de 2 cm."""
    image = _strand_texture()
    mask = np.zeros(image.shape[:2], dtype=bool)
    mask[100:800, 100:800] = True
    without_scale = extract_features(image, mask)
    with_scale = extract_features(image, mask, pixels_per_cm=40.0)
    assert without_scale.curl_diameter_mm is None
    assert with_scale.curl_diameter_mm is not None
    # Las métricas relativas sí se pueden calcular sin escala.
    assert without_scale.frizz_index is not None


def test_feature_extraction_rejects_a_mismatched_mask() -> None:
    with pytest.raises(ValueError):
        extract_features(_strand_texture(200), np.zeros((100, 100), dtype=bool))
