
from sqlalchemy import Column, Integer, String, Date, Enum, DECIMAL
from .database import Base
import enum

class InvoiceStatus(enum.Enum):
    not_paid = "not_paid"
    paid = "paid"
    deleted = "deleted"
    pending = "pending"

class CustomerInfo(Base):
    __tablename__ = "customer_info"

    customer_id = Column(Integer, primary_key=True)
    passport = Column(String(64))

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer)
    number = Column(String(64))
    date_created = Column(Date)
    date_till = Column(Date)
    due = Column(DECIMAL(19, 4))
    total = Column(DECIMAL(19, 4))
    status = Column(Enum(InvoiceStatus))
