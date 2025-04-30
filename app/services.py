# from sqlalchemy.orm import Session
# from sqlalchemy import func
# import re
# from .models import CustomerInfo, Invoice
# from datetime import date
# import uuid

# def normalizar_rut(rut: str) -> str:
#     return re.sub(r'[^0-9kK]', '', rut).lower().strip()

# def get_client_debt_by_rut(db: Session, rut: str):
#     rut_normalizado = normalizar_rut(rut)

#     clientes_info = db.query(CustomerInfo).filter(
#         func.replace(func.replace(func.lower(CustomerInfo.passport), '.', ''), '-', '') == rut_normalizado
#     ).all()

#     if not clientes_info:
#         return {
#             "detalle": "Cliente no encontrado"
#         }

#     customer_ids = [cliente.customer_id for cliente in clientes_info]

#     invoices = db.query(Invoice).filter(
#         Invoice.customer_id.in_(customer_ids),
#         Invoice.status == "not_paid",
#         Invoice.deleted == "0"
#     ).all()

#     if not invoices:
#         return {
#             "rut_cliente": clientes_info[0].passport,
#             "nombre_cliente": clientes_info[0].customer.name if clientes_info[0].customer else "No disponible",
#             "numero_orden": str(uuid.uuid4()),
#             "mensaje": "El cliente no posee deudas vigentes."
#         }

#     total_debt = 0
#     expired_debt = 0
#     boletas = []

#     for invoice in invoices:
#         monto = float(invoice.total or 0)
#         vencido = invoice.date_till < date.today()
#         total_debt += monto
#         if vencido:
#             expired_debt += monto

#         boletas.append({
#             "id_boleta": invoice.id,
#             "numero_boleta": invoice.number,
#             "periodo": f"{invoice.date_created} - {invoice.date_till}",
#             "monto": monto,
#             "fecha_vencimiento": str(invoice.date_till),
#             "customer_id": invoice.customer_id,
#             "vencido": vencido
#         })

#     return {
#         "rut_cliente": clientes_info[0].passport,
#         "nombre_cliente": clientes_info[0].customer.name if clientes_info[0].customer else "No disponible",
#         "monto_deuda_total": total_debt,
#         "monto_deuda_vencida": expired_debt,
#         "numero_orden": str(uuid.uuid4()),
#         "boletas": boletas
#     }


# def guardar_boletas_en_db(db: Session, boletas: list, numero_orden: str):
#     for b in boletas:
#         invoice = BancoEstadoInvoice(
#             id_boleta=b["id_boleta"],
#             numero_orden=numero_orden,
#             numero_boleta=b["numero_boleta"],
#             monto=int(b["monto"]),
#             payment_id=None,
#             transaction_id=None,
#             vencido=b.get("vencido", False)
#         )
#         db.merge(invoice)  # merge evita conflictos si ya existe la boleta
#     db.commit()


# from sqlalchemy.orm import Session
# from sqlalchemy import func
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import text, select
# import re
# from app.models import CustomerInfo, Invoice, BancoEstadoInvoice, BancoEstadoData
# from app.local_database import LocalSession
# from datetime import date
# from starlette import status
# import uuid
# from fastapi import HTTPException
# from app.schema import NotificacionPagoRequest 
# from app.helpers.rabbitmq_client import RabbitMQClient
# import json

# def normalizar_rut(rut: str) -> str:
#     return re.sub(r'[^0-9kK]', '', rut).lower().strip()

# def get_client_debt_by_rut(db: Session, rut: str) -> dict:
#     try:
#         rut_norm = normalizar_rut(rut)
        
#         clientes = db.execute(
#             text("CALL splynx.buscar_cliente_por_rut(:rut)"),
#             {"rut": rut_norm}
#         ).mappings().all()

#         if not clientes:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail={"error": "client_not_found", "message": "Cliente no encontrado"}
#             )
        
#         invoices = db.execute(
#             text("CALL splynx.consultar_deuda_cliente(:rut)"),
#             {"rut": rut_norm}
#         ).mappings().all()

#         order_id = str(uuid.uuid4())

#         if not invoices:
#             resp = {
#                 "rut_cliente": rut_norm,
#                 "nombre_cliente": clientes[0]["nombre_cliente"],
#                 "numero_orden": order_id,
#                 "mensaje": "El cliente no posee deudas vigentes."
#             }
#             # guardar_en_bd_local(resp)
#             return resp
        
#         total = sum(int(inv["total"] or 0) for inv in invoices)
#         vencido = sum(int(inv["total"] or 0) for inv in invoices if inv["vencido"])
#         boletas = [
#             {
#                 "id_boleta": inv["invoice_id"],
#                 "numero_boleta": inv["numero_boleta"],
#                 "periodo": f"{inv['fecha_creacion']} - {inv['fecha_vencimiento']}",
#                 "monto": int(inv["total"] or 0),
#                 "fecha_vencimiento": inv["fecha_vencimiento"].isoformat(),
#                 "customer_id": inv["id_cliente"],
#                 "vencido": inv["vencido"]
#             }
#             for inv in invoices
#         ]

#         resp = {
#             "rut_cliente": rut_norm,
#             "nombre_cliente": clientes[0]["nombre_cliente"],
#             "monto_deuda_total": total,
#             "monto_deuda_vencida": vencido,
#             "numero_orden": order_id,
#             "boletas": boletas
#         }

#         guardar_en_bd_local(resp)
#         return resp
    
#     except HTTPException:
#         raise
#     except SQLAlchemyError as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"error": "database_error", "message": str(e)}
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"error": "internal_error", "message": str(e)}
#         )

# def guardar_en_bd_local(response_data: dict):
#     local_db = LocalSession()
#     try:
#         be_data = BancoEstadoData(
#             numero_orden=response_data["numero_orden"],
#             monto_deuda_total=int(response_data.get("monto_deuda_total", 0)),
#             monto_deuda_vencida=int(response_data.get("monto_deuda_vencida", 0)),
#             fecha_pago=None,
#             fecha_contable=None,
#             canal_pago=None,
#             estado=None,
#             monto_pagado=None,
#             socio=None
#         )
#         local_db.add(be_data)

#         for b in response_data.get("boletas", []):
#             invoice = BancoEstadoInvoice(
#                 id_boleta=b["id_boleta"],
#                 numero_orden=response_data["numero_orden"],
#                 numero_boleta=b["numero_boleta"],
#                 monto=int(b["monto"]),
#                 payment_id=None,
#                 transaction_id=None,
#                 vencido=b.get("vencido", False)
#             )
#             local_db.merge(invoice)

#         local_db.commit()
#     except Exception as e:
#         local_db.rollback()
#         raise e
#     finally:
#         local_db.close()

# async def notificar_pago(rabbitmq: RabbitMQClient, db: Session, request: NotificacionPagoRequest):
#     be_data = db.query(BancoEstadoData).filter_by(numero_orden=request.numero_orden).first()
#     if not be_data:
#         return {"status": "CLIENTE_NO_EXISTE"}

#     boletas = db.query(BancoEstadoInvoice).filter_by(numero_orden=request.numero_orden).all()
#     if not boletas:
#         return {"status": "CLIENTE_NO_EXISTE"}

#     monto_total = sum([b.monto for b in boletas])
#     monto_vencido = sum([b.monto for b in boletas if b.vencido])

#     if request.monto_pagado == monto_total:
#         pago_tipo = "total"
#     elif request.monto_pagado == monto_vencido:
#         pago_tipo = "vencido"
#     else:
#         return {"status": "MONTO_NO_COINCIDE"}

#     be_data.fecha_pago = request.fecha_pago
#     be_data.fecha_contable = request.fecha_contable
#     be_data.canal_pago = request.canal_pago
#     be_data.estado = request.estado
#     be_data.monto_pagado = request.monto_pagado

#     db.commit()

#     boletas_pagadas = boletas if pago_tipo == "total" else [b for b in boletas if b.vencido]

#     for boleta in boletas_pagadas:
#         msg = {
#             "numero_orden": request.numero_orden,
#             "splynx_domain": "micuenta.netxtreme.cl/bancoestado",
#             "invoice_id": boleta.id_boleta,
#             "canal_pago": request.canal_pago,
#             "socio": "Nx"
#         }
#         try:
#             await rabbitmq.send_message("bancoestado_invoices", msg)
#         except Exception:
#             return {"status": "ERROR_INTERNO"}

#     return {
#         "status": "OK",
#         "numero_orden": request.numero_orden,
#         "tipo_pago": pago_tipo
#     }


from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
import re
import uuid
from datetime import date
from app.models import CustomerInfo, Invoice, BancoEstadoInvoice, BancoEstadoData
from app.local_database import LocalSession
from fastapi import HTTPException
from app.schema import NotificacionPagoRequest
from app.helpers.rabbitmq_client import RabbitMQClient

def normalizar_rut(rut: str) -> str:
    return re.sub(r'[^0-9kK]', '', rut).lower().strip()

def get_client_debt_by_rut(db: Session, rut: str) -> dict:
    try:
        rut_norm = normalizar_rut(rut)
        
        clientes = db.execute(
            text("CALL splynx.buscar_cliente_por_rut(:rut)"),
            {"rut": rut_norm}
        ).mappings().all()

        if not clientes:
            raise HTTPException(
                status_code=404,
                detail={"error": "client_not_found", "message": "Cliente no encontrado"}
            )
        
        invoices = db.execute(
            text("CALL splynx.consultar_deuda_cliente(:rut)"),
            {"rut": rut_norm}
        ).mappings().all()

        order_id = str(uuid.uuid4())

        if not invoices:
            return {
                "rut_cliente": rut_norm,
                "nombre_cliente": clientes[0]["nombre_cliente"],
                "numero_orden": order_id,
                "mensaje": "El cliente no posee deudas vigentes."
            }
        
        total = sum(int(inv["total"] or 0) for inv in invoices)
        vencido = sum(int(inv["total"] or 0) for inv in invoices if inv["vencido"])
        boletas = [
            {
                "id_boleta": inv["invoice_id"],
                "numero_boleta": inv["numero_boleta"],
                "periodo": f"{inv['fecha_creacion']} - {inv['fecha_vencimiento']}",
                "monto": int(inv["total"] or 0),
                "fecha_vencimiento": inv["fecha_vencimiento"].isoformat(),
                "customer_id": inv["id_cliente"],
                "vencido": inv["vencido"]
            }
            for inv in invoices
        ]

        resp = {
            "rut_cliente": rut_norm,
            "nombre_cliente": clientes[0]["nombre_cliente"],
            "monto_deuda_total": total,
            "monto_deuda_vencida": vencido,
            "numero_orden": order_id,
            "boletas": boletas
        }

        guardar_en_bd_local(resp)
        return resp
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "database_error", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )

def guardar_en_bd_local(response_data: dict):
    local_db = LocalSession()
    try:
        be_data = BancoEstadoData(
            numero_orden=response_data["numero_orden"],
            monto_deuda_total=int(response_data.get("monto_deuda_total", 0)),
            monto_deuda_vencida=int(response_data.get("monto_deuda_vencida", 0)),
            fecha_pago=None,
            fecha_contable=None,
            canal_pago=None,
            estado=None,
            monto_pagado=None,
            socio=None
        )
        local_db.add(be_data)

        for b in response_data.get("boletas", []):
            invoice = BancoEstadoInvoice(
                id_boleta=b["id_boleta"],
                numero_orden=response_data["numero_orden"],
                numero_boleta=b["numero_boleta"],
                monto=int(b["monto"]),
                payment_id=None,
                transaction_id=None,
                vencido=b.get("vencido", False)
            )
            local_db.merge(invoice)

        local_db.commit()
    except Exception as e:
        local_db.rollback()
        raise e
    finally:
        local_db.close()

async def notificar_pago(rabbitmq: RabbitMQClient, db: Session, request: NotificacionPagoRequest):
    try:
        be_data = db.query(BancoEstadoData).filter_by(numero_orden=request.numero_orden).first()
        if not be_data:
            return {"status": "CLIENTE_NO_EXISTE"}

        boletas = db.query(BancoEstadoInvoice).filter_by(numero_orden=request.numero_orden).all()
        if not boletas:
            return {"status": "CLIENTE_NO_EXISTE"}

        monto_total = sum([b.monto for b in boletas])
        monto_vencido = sum([b.monto for b in boletas if b.vencido])

        if request.monto_pagado == monto_total:
            pago_tipo = "total"
        elif request.monto_pagado == monto_vencido:
            pago_tipo = "vencido"
        else:
            return {"status": "MONTO_NO_COINCIDE"}

        be_data.fecha_pago = request.fecha_pago
        be_data.fecha_contable = request.fecha_contable
        be_data.canal_pago = request.canal_pago
        be_data.estado = request.estado
        be_data.monto_pagado = request.monto_pagado
        db.commit()

        boletas_pagadas = boletas if pago_tipo == "total" else [b for b in boletas if b.vencido]

        for boleta in boletas_pagadas:
            msg = {
                "numero_orden": request.numero_orden,
                "splynx_domain": "micuenta.netxtreme.cl/bancoestado",
                "invoice_id": boleta.id_boleta,
                "canal_pago": request.canal_pago,
                "socio": "Nx"
            }
            try:
                await rabbitmq.send_message("bancoestado_invoices", msg)
            except Exception:
                return {"status": "ERROR_INTERNO"}

        return {
            "status": "OK",
            "numero_orden": request.numero_orden,
            "tipo_pago": pago_tipo
        }

    except Exception as e:
        return {"status": "ERROR_INTERNO", "error": str(e)}
