"""Almacenamiento de fotos.

Las imágenes nunca viven en la base de datos: el bucket es privado y el acceso
va por URL prefirmada de vida corta. El backend no sirve las imágenes.

La implementación por defecto es local y está pensada para desarrollo y tests.
`S3Storage` queda como el hueco a rellenar con boto3 y el bucket real; la
interfaz no cambia.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.hair import Scan, ScanPhotoRow
from ..models.products import JournalRow
from ..models.user import User


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> str: ...

    def presigned_url(self, key: str) -> str: ...

    def delete(self, key: str) -> None: ...

    def delete_prefix(self, prefix: str) -> int: ...


class LocalStorage:
    """Almacenamiento en disco para desarrollo y tests.

    No es el almacenamiento de producción y no pretende serlo: no cifra en
    reposo ni caduca las URL. Se usa para que el flujo completo se pueda
    ejecutar sin depender de un servicio externo.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(".storage")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        target = (self.root / key).resolve()
        root = self.root.resolve()
        if not str(target).startswith(str(root)):
            raise ValueError("clave de almacenamiento fuera del directorio raíz")
        return target

    def put(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def presigned_url(self, key: str) -> str:
        return f"file://{self._path(key)}"

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def delete_prefix(self, prefix: str) -> int:
        directory = self._path(prefix)
        if not directory.exists():
            return 0
        count = sum(1 for _ in directory.rglob("*") if _.is_file())
        shutil.rmtree(directory)
        return count


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage


def set_storage(storage: Storage) -> None:
    """Punto de inyección para tests y para enchufar S3 en producción."""
    global _storage
    _storage = storage


def photo_key(user_id: str, scan_id: str, angle: str) -> str:
    return f"users/{user_id}/scans/{scan_id}/{angle}.jpg"


def user_prefix(user_id: str) -> str:
    return f"users/{user_id}"


def purge_user_objects(session: Session, user: User) -> int:
    """Borra todos los objetos de una persona antes de eliminar sus filas.

    Se hace explícitamente en vez de confiar en la cascada de la base de datos:
    la cascada borra filas, no archivos, y dejar las fotos en el bucket tras un
    borrado de cuenta incumple el compromiso de A22.
    """
    storage = get_storage()

    keys: list[str] = []
    scan_ids = (
        session.execute(
            select(Scan.id).join(Scan.profile).where(Scan.profile.has(user_id=user.id))
        )
        .scalars()
        .all()
    )
    if scan_ids:
        keys += (
            session.execute(
                select(ScanPhotoRow.storage_key).where(ScanPhotoRow.scan_id.in_(scan_ids))
            )
            .scalars()
            .all()
        )
    journal_photo_lists = (
        session.execute(
            select(JournalRow.photo_keys).where(
                JournalRow.profile_id.in_(
                    select(Scan.profile_id).where(Scan.id.in_(scan_ids))
                )
            )
        )
        .scalars()
        .all()
    )
    for group in journal_photo_lists:
        keys += list(group or ())

    for key in keys:
        storage.delete(key)

    # Y además se borra el prefijo entero, por si quedó algún objeto huérfano
    # que ninguna fila referenciaba.
    return storage.delete_prefix(user_prefix(user.id)) + len(keys)
