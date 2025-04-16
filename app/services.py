from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import re
from .models import CustomerInfo, Invoice
from datetime import date

def normalizar_rut(rut: str) -> str:
    return re.sub(r'[^0-9kK]', '', rut).lower().strip()

def get_client_debt_by_rut(db: Session, rut: str):
    rut_normalizado = normalizar_rut(rut)

    clientes_info = db.query(CustomerInfo).options(
        joinedload(CustomerInfo.customer)
    ).filter(
        func.replace(func.replace(func.lower(CustomerInfo.passport), '.', ''), '-', '') == rut_normalizado
    ).all()

    if not clientes_info:
        return None

    customer_ids = [cliente.customer_id for cliente in clientes_info]

    invoices = db.query(Invoice).filter(
        Invoice.customer_id.in_(customer_ids),
        Invoice.status == "not_paid",
        Invoice.deleted == "0"
    ).all()

    total_debt = 0
    boletas = []

    for invoice in invoices:
        monto = float(invoice.total or 0)
        total_debt += monto

        boletas.append({
            "id_boleta": invoice.id,
            "numero_boleta": invoice.number,
            "periodo": f"{invoice.date_created} - {invoice.date_till}",
            "monto": monto,
            "fecha_vencimiento": str(invoice.date_till),
            "customer_id": invoice.customer_id
        })

    return {
        "rut_cliente": clientes_info[0].passport,
        "nombre_cliente": clientes_info[0].customer.name if clientes_info[0].customer else "No disponible",
        "monto_deuda_total": total_debt,
        "numero_orden": ", ".join([str(cid) for cid in customer_ids]),
        "boletas": boletas
    }
