from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from fastapi.responses import JSONResponse
from app.database import SessionLocal
from app.local_database import LocalSession
from app.services import get_client_debt_by_rut, notificar_pago
from app.middlewares.jwt_auth import JWTValidationMiddleware
from app.helpers.rabbitmq_client import RabbitMQClient
from contextlib import asynccontextmanager

rabbitmq = RabbitMQClient(queues=["bancoestado_invoices"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Conecta a RabbitMQ antes de arrancar el servidor
    await rabbitmq.connect()
    yield
    # --- Shutdown ---
    # Cierra la conexión de forma limpia
    if rabbitmq.connection and not rabbitmq.connection.is_closed:
        await rabbitmq.connection.close()


app = FastAPI(lifespan=lifespan)
# app.add_middleware(JWTValidationMiddleware)


class DeudaRequest(BaseModel):
    rut_cliente: str

class NotificacionPagoRequest(BaseModel):
    numero_orden: str
    monto_pagado: int
    fecha_pago: Optional[date] = None
    fecha_contable: Optional[date] = None
    canal_pago: Optional[str] = None
    estado: Optional[str] = None

def get_splynx_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_local_db():
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()

@app.post("/consultar-deuda")
async def consultar_deuda(request: DeudaRequest, db: Session = Depends(get_splynx_db)):
    resultado = get_client_debt_by_rut(db, request.rut_cliente)
    if "detalle" in resultado and resultado["detalle"] == "Cliente no encontrado":
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado

@app.post("/notificacion-pago")
async def notificacion_pago(request: NotificacionPagoRequest, db: Session = Depends(get_local_db)):
    return await notificar_pago(rabbitmq, db, request)
