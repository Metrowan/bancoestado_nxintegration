from sqlalchemy.orm import Session
from sqlalchemy import func
import re
from .models import CustomerInfo, Invoice
from datetime import date

def normalizar_rut(rut: str) -> str:
    """Elimina puntos, guiones y lo convierte a minúsculas."""
    return re.sub(r'[^0-9kK]', '', rut).lower().strip()

def get_client_debt_by_rut(db: Session, rut: str):
    rut_normalizado = normalizar_rut(rut)
    print("🔍 Buscando RUT normalizado:", rut_normalizado)

    customer_info = db.query(CustomerInfo).filter(
        func.replace(func.replace(func.lower(CustomerInfo.passport), '.', ''), '-', '') == rut_normalizado
    ).first()

    if not customer_info:
        return None

    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_info.customer_id,
        Invoice.status.notin_(["paid", "deleted"])
    ).all()

    total_debt = 0
    expired_debt = 0
    boletas = []

    for invoice in invoices:
        is_expired = invoice.date_till < date.today()
        monto = float(invoice.total or 0)

        total_debt += monto
        if is_expired:
            expired_debt += monto

        boletas.append({
            "id_boleta": invoice.id,
            "numero_boleta": invoice.number,
            "periodo": f"{invoice.date_created} - {invoice.date_till}",
            "monto": monto,
            "fecha_vencimiento": str(invoice.date_till),
            "vencido": is_expired
        })

    return {
        "rut_cliente": customer_info.passport,
        "nombre_cliente": "No disponible",
        "monto_deuda_total": total_debt,
        "monto_deuda_vencida": expired_debt,
        "numero_orden": str(customer_info.customer_id),
        "boletas": boletas
    }
