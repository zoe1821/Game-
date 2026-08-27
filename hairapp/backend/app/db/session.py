"""Unidad de trabajo por petición.

**El problema que resuelve.** Con el patrón habitual de `yield session` y
`session.commit()` en el bloque de limpieza, el commit ocurre *después* de que
la respuesta ya se ha generado. Eso produce dos fallos reales:

  1. El cliente recibe `204 No Content` de un borrado de cuenta y, si vuelve a
     preguntar inmediatamente, la cuenta todavía existe.
  2. Si el commit falla, el cliente ya recibió un `201` diciendo que todo fue
     bien. Se le ha mentido, y no hay forma de corregirlo.

**La solución.** Una clase de ruta que envuelve al manejador: ejecuta el
endpoint, hace commit, y solo entonces devuelve la respuesta. Si el commit
falla, el error ocurre antes de responder y el cliente recibe un 500 honesto.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine, Iterator
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from .base import get_session_factory

#: Dónde vive la sesión durante la petición, para que la ruta pueda cerrarla.
STATE_ATTRIBUTE = "db_session"


def get_db(request: Request) -> Iterator[Session]:
    """Sesión de base de datos ligada a la petición.

    No hace commit: de eso se encarga `TransactionalRoute`, que sí puede
    hacerlo antes de devolver la respuesta.
    """
    session = get_session_factory()()
    setattr(request.state, STATE_ATTRIBUTE, session)
    try:
        yield session
    except Exception:
        session.rollback()
        raise


class TransactionalRoute(APIRoute):
    """Confirma la transacción **antes** de devolver la respuesta."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            try:
                response = await original(request)
            except Exception:
                _finish(request, commit=False)
                raise
            # Si el commit falla aquí, la excepción se propaga y el cliente
            # recibe un error, que es la verdad. Nunca un 2xx sobre datos que
            # no se guardaron.
            _finish(request, commit=True)
            return response

        return handler


def _finish(request: Request, *, commit: bool) -> None:
    session: Session | None = getattr(request.state, STATE_ATTRIBUTE, None)
    if session is None:
        return
    try:
        if commit:
            session.commit()
        else:
            session.rollback()
    finally:
        session.close()
        setattr(request.state, STATE_ATTRIBUTE, None)
