"""Flujo de scan.

El consentimiento de procesamiento de fotos se exige aquí y **solo** aquí: sin
él, el resto de la app sigue funcionando entera (A22).
"""

from __future__ import annotations

import io
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from PIL import Image

from ...core.errors import Forbidden, NotFound, ValidationFailed
from ...db.base import utcnow
from ...db.session import TransactionalRoute
from ...domain.billing.entitlements import Feature
from ...domain.hair.zones import ALL_ZONES, PhotoAngle, coverage_for
from ...domain.scan.pipeline import ScanPhoto
from ...domain.scan.quality import assess_photo
from ...models.hair import Scan, ScanPhotoRow, ScanStatus
from ...models.user import ConsentPurpose, User
from ...services.billing_service import record_usage, require
from ...services.engine import get_scan_pipeline
from ...services.profile_service import apply_estimates, ensure_zones, get_zone
from ...services.storage import get_storage, photo_key
from ..deps import CurrentProfile, DbSession, require_consent

router = APIRouter(prefix="/scans", tags=["scans"], route_class=TransactionalRoute)

MAX_UPLOAD_BYTES = 12 * 1024 * 1024

PhotoConsent = Annotated[User, Depends(require_consent(ConsentPurpose.PHOTO_PROCESSING))]


def _decode(data: bytes) -> np.ndarray:
    try:
        with Image.open(io.BytesIO(data)) as image:
            return np.asarray(image.convert("RGB"), dtype=np.float64)
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de decodificación
        raise ValidationFailed("error.unreadable_image") from exc


@router.get("/required-angles")
def required_angles() -> dict[str, object]:
    """Qué fotos pide el flujo y qué zonas cubre cada una.

    Se expone para que la app pueda decir de antemano qué se verá y qué no,
    en vez de descubrirlo al final.
    """
    return {
        "angles": [
            {
                "angle": angle.value,
                "required": angle.is_required,
                "label_key": f"scan.angle.{angle.value}",
                "covers_zones": [z.value for z in coverage_for([angle]).covered],
            }
            for angle in PhotoAngle
        ],
        "total_zones": len(ALL_ZONES),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_scan(profile: CurrentProfile, session: DbSession, user: PhotoConsent) -> dict[str, object]:
    """Inicia un scan, si el plan lo permite.

    El cupo se comprueba aquí, antes de que la persona haga las fotos: descubrir
    que no te queda cupo después de fotografiarte ocho ángulos sería una falta
    de respeto por su tiempo.
    """
    decision = require(session, user.id, Feature.SCAN)

    scan = Scan(profile_id=profile.id, status=ScanStatus.DRAFT)
    session.add(scan)
    session.flush()
    return {"id": scan.id, "status": scan.status.value, "entitlement": decision.as_dict()}


@router.post("/{scan_id}/photos")
async def upload_photo(
    scan_id: str,
    profile: CurrentProfile,
    user: PhotoConsent,
    session: DbSession,
    file: Annotated[UploadFile, File()],
    angle: Annotated[str, Form()],
    face_cropped: Annotated[bool, Form()] = False,
) -> dict[str, object]:
    """Sube una foto y devuelve su calidad al momento.

    La calidad se evalúa aquí además de en el dispositivo: así la app puede
    pedir repetir **solo esta** foto, sin esperar al análisis completo (A3).
    """
    scan = session.get(Scan, scan_id)
    if scan is None or scan.profile_id != profile.id:
        raise NotFound("scan", scan_id=scan_id)

    try:
        parsed_angle = PhotoAngle(angle)
    except ValueError as exc:
        raise ValidationFailed("error.unknown_angle", angle=angle) from exc

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationFailed("error.image_too_large", max_bytes=MAX_UPLOAD_BYTES)

    image = _decode(data)
    report = assess_photo(image, parsed_angle)

    key = photo_key(user.id, scan.id, parsed_angle.value)
    get_storage().put(key, data)

    existing = next((p for p in scan.photos if p.angle == parsed_angle.value), None)
    if existing is not None:
        existing.storage_key = key
        existing.quality = report.as_dict()
        existing.face_cropped = face_cropped
        session.add(existing)
    else:
        session.add(
            ScanPhotoRow(
                scan_id=scan.id,
                angle=parsed_angle.value,
                storage_key=key,
                quality=report.as_dict(),
                face_cropped=face_cropped,
            )
        )
    session.flush()
    return report.as_dict()


@router.post("/{scan_id}/analyse")
def analyse_scan(
    scan_id: str, profile: CurrentProfile, user: PhotoConsent, session: DbSession
) -> dict[str, object]:
    """Ejecuta el pipeline.

    Si la segmentación no está disponible (hoy es un mock declarado), el
    resultado lo dice y no produce estimaciones de imagen. Ver
    docs/07-SCANNER-PIPELINE.md.
    """
    scan = session.get(Scan, scan_id)
    if scan is None or scan.profile_id != profile.id:
        raise NotFound("scan", scan_id=scan_id)
    if not scan.photos:
        raise ValidationFailed("error.scan_has_no_photos")

    storage = get_storage()
    photos: list[ScanPhoto] = []
    for row in scan.photos:
        try:
            path = storage.presigned_url(row.storage_key).removeprefix("file://")
            with Image.open(path) as image:
                array = np.asarray(image.convert("RGB"), dtype=np.float64)
        except (OSError, ValueError):
            continue
        photos.append(ScanPhoto(angle=PhotoAngle(row.angle), image=array))

    if not photos:
        raise ValidationFailed("error.scan_photos_unreadable")

    result = get_scan_pipeline().run(photos)
    scan.quality_report = result.quality.as_dict()
    scan.interpretation = result.as_dict()
    scan.status = ScanStatus.AWAITING_CONFIRMATION
    session.add(scan)

    # El cupo se descuenta aquí, con el análisis ya hecho. Descontarlo al crear
    # el scan cobraría por un intento que quizá nunca llegó a analizarse.
    record_usage(session, user.id, Feature.SCAN)

    return result.as_dict()


@router.post("/{scan_id}/confirm")
def confirm_scan(
    scan_id: str,
    profile: CurrentProfile,
    session: DbSession,
    corrections: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    """Confirmación obligatoria (A1.4).

    Nada entra al perfil hasta este momento. `corrections` permite corregir
    zona por zona; lo corregido queda con fuente `user` y ya no se sobrescribe.
    """
    from datetime import date

    from ...domain.common import Measured, Source
    from ...domain.hair.zones import Zone
    from ...services.profile_service import set_user_value

    scan = session.get(Scan, scan_id)
    if scan is None or scan.profile_id != profile.id:
        raise NotFound("scan", scan_id=scan_id)
    if scan.status is not ScanStatus.AWAITING_CONFIRMATION:
        raise Forbidden("error.scan_not_ready_for_confirmation", status=scan.status.value)

    ensure_zones(session, profile)
    today = date.today()
    outcomes: dict[str, dict[str, str]] = {}

    estimates = (scan.interpretation or {}).get("estimates", {})
    for zone_value, fields in estimates.items():
        zone_row = get_zone(session, profile.id, Zone(zone_value))
        if zone_row is None:
            continue
        measured = {
            field: Measured(
                value=payload["value"],
                source=Source(payload["source"]),
                confidence=float(payload["confidence"]),
                observed_at=today,
            )
            for field, payload in fields.items()
        }
        outcomes[zone_value] = apply_estimates(session, zone_row, measured)

    for zone_value, fields in (corrections or {}).items():
        try:
            zone = Zone(zone_value)
        except ValueError as exc:
            raise ValidationFailed("error.unknown_zone", zone=zone_value) from exc
        zone_row = get_zone(session, profile.id, zone)
        if zone_row is None:
            continue
        for field, value in fields.items():
            set_user_value(session, zone_row, field, value)
            outcomes.setdefault(zone_value, {})[field] = "user_correction"

    scan.status = ScanStatus.CONFIRMED
    scan.confirmed_at = utcnow()
    session.add(scan)

    from ...services.profile_service import compute_completeness

    profile.completeness = compute_completeness(profile)
    session.add(profile)

    return {"scan_id": scan.id, "status": scan.status.value, "outcomes": outcomes}
