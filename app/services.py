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


from sqlalchemy.orm import Session
from sqlalchemy import func
import re
from .models import CustomerInfo, Invoice, BancoEstadoInvoice, BancoEstadoData
from .local_database import LocalSession
from datetime import date
import uuid

def normalizar_rut(rut: str) -> str:
    return re.sub(r'[^0-9kK]', '', rut).lower().strip()

def get_client_debt_by_rut(db: Session, rut: str):
    rut_normalizado = normalizar_rut(rut)

    clientes_info = db.query(CustomerInfo).filter(
        func.replace(func.replace(func.lower(CustomerInfo.passport), '.', ''), '-', '') == rut_normalizado
    ).all()

    if not clientes_info:
        return {
            "detalle": "Cliente no encontrado"
        }

    customer_ids = [cliente.customer_id for cliente in clientes_info]

    invoices = db.query(Invoice).filter(
        Invoice.customer_id.in_(customer_ids),
        Invoice.status == "not_paid",
        Invoice.deleted == "0"
    ).all()

    numero_orden = str(uuid.uuid4())

    if not invoices:
        response = {
            "rut_cliente": clientes_info[0].passport,
            "nombre_cliente": clientes_info[0].customer.name if clientes_info[0].customer else "No disponible",
            "numero_orden": numero_orden,
            "mensaje": "El cliente no posee deudas vigentes."
        }
        guardar_en_bd_local(response)
        return response

    total_debt = 0
    expired_debt = 0
    boletas = []

    for invoice in invoices:
        monto = float(invoice.total or 0)
        vencido = invoice.date_till < date.today()
        total_debt += monto
        if vencido:
            expired_debt += monto

        boletas.append({
            "id_boleta": invoice.id,
            "numero_boleta": invoice.number,
            "periodo": f"{invoice.date_created} - {invoice.date_till}",
            "monto": monto,
            "fecha_vencimiento": str(invoice.date_till),
            "customer_id": invoice.customer_id,
            "vencido": vencido
        })

    response = {
        "rut_cliente": clientes_info[0].passport,
        "nombre_cliente": clientes_info[0].customer.name if clientes_info[0].customer else "No disponible",
        "monto_deuda_total": total_debt,
        "monto_deuda_vencida": expired_debt,
        "numero_orden": numero_orden,
        "boletas": boletas
    }

    guardar_en_bd_local(response)
    return response

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
