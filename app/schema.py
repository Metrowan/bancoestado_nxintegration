from pydantic import BaseModel
from datetime import date
from typing import Optional

class NotificacionPagoRequest(BaseModel):
    numero_orden: str
    monto_pagado: int
    fecha_pago: Optional[date]
    fecha_contable: Optional[date]
    canal_pago: Optional[str]
    estado: Optional[str]
