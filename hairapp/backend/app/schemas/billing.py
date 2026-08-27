from __future__ import annotations

from pydantic import Field

from .common import ApiModel


class ActivateIn(ApiModel):
    """Lo que el cliente manda al activar.

    Solo `token` importa de verdad: es lo que se manda a verificar y lo único
    que el cliente no puede falsificar. El resto se conserva para contrastar y
    para diagnóstico, pero **el plan y la fecha de fin salen de la respuesta de
    la tienda**, nunca de aquí.
    """

    store: str
    token: str = Field(min_length=8)
    product_id: str
    transaction_id: str
    billing_country: str | None = Field(default=None, max_length=2)
