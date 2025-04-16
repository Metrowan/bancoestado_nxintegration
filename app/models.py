from sqlalchemy import Column, Integer, String, Date, Enum, DECIMAL
from sqlalchemy.orm import relationship, foreign
from .database import Base
import enum

class InvoiceStatus(enum.Enum):
    not_paid = "not_paid"
    paid = "paid"
    deleted = "deleted"
    pending = "pending"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    deleted = Column(Enum("1", "0"), default="0")

    # No declaramos back_populates porque no hay ForeignKey real


class CustomerInfo(Base):
    __tablename__ = "customer_info"

    customer_id = Column(Integer, primary_key=True)
    passport = Column(String(64))

    customer = relationship(
        "Customer",
        primaryjoin="Customer.id==foreign(CustomerInfo.customer_id)",
        viewonly=True,
        uselist=False
    )


class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False)
    number = Column(String(64), nullable=False)
    date_created = Column(Date)
    date_till = Column(Date)
    total = Column(DECIMAL(19, 4))
    status = Column(Enum('not_paid', 'paid', 'deleted', 'pending'), default='not_paid', nullable=False)
    deleted = Column(Enum('0', '1'), default='0', nullable=False)  # <- ⚠️ ESTA LÍNEA ES CLAVE
