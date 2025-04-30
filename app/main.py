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
from datetime import datetime

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
    try:
        resultado = get_client_debt_by_rut(db, request.rut_cliente)

        # Caso: Cliente no identificado
        if "detalle" in resultado and resultado["detalle"] == "Cliente no encontrado":
            return JSONResponse(status_code=200, content={
                "ERR_CODE": "3",
                "ERR_MESSAGE": "RUT no identificado"
            })

        # Caso: RUT sin deudas
        if resultado.get("deuda_total", 0) == 0:
            return JSONResponse(status_code=200, content={
                "ERR_CODE": "4",
                "ERR_MESSAGE": "RUT sin deudas"
            })

        # Caso OK
        return JSONResponse(status_code=200, content={
            "ERR_CODE": "0",
            "ERR_MESSAGE": "OK",
            "data": resultado
        })

    except Exception as e:
        # Error interno
        return JSONResponse(status_code=500, content={
            "ERR_CODE": "1",
            "ERR_MESSAGE": f"Error interno del servidor: {str(e)}"
        })


@app.post("/notificacion-pago")
async def notificacion_pago(request: NotificacionPagoRequest, db: Session = Depends(get_local_db)):
    try:
        resultado = await notificar_pago(rabbitmq, db, request)

        # Validación personalizada desde la lógica de negocio
        if resultado.get("status") == "CLIENTE_NO_EXISTE":
            return JSONResponse(status_code=200, content={
                "ERR_CODE": "3",
                "ERR_MESSAGE": "CLIENTE NO EXISTE",
                "RUT_CLIENTE": request.numero_orden,
                "FECHA_RECEPCION": datetime.now().isoformat(),
                "ESTADO_CONFIRMACION": "NOK"
            })

        elif resultado.get("status") == "MONTO_NO_COINCIDE":
            return JSONResponse(status_code=200, content={
                "ERR_CODE": "5",
                "ERR_MESSAGE": "MONTO PAGADO NO COINCIDE CON LA DEUDA ACTUAL DEL CLIENTE",
                "RUT_CLIENTE": request.numero_orden,
                "FECHA_RECEPCION": datetime.now().isoformat(),
                "ESTADO_CONFIRMACION": "NOK"
            })

        # Caso exitoso
        return JSONResponse(status_code=200, content={
            "ERR_CODE": "0",
            "ERR_MESSAGE": "OK",
            "RUT_CLIENTE": request.numero_orden,
            "FECHA_RECEPCION": datetime.now().isoformat(),
            "ESTADO_CONFIRMACION": "OK"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "ERR_CODE": "1",
            "ERR_MESSAGE": f"Error interno del servidor: {str(e)}",
            "RUT_CLIENTE": request.numero_orden,
            "FECHA_RECEPCION": datetime.now().isoformat(),
            "ESTADO_CONFIRMACION": "NOK"
        })
