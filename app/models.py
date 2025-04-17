from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))

    # Relación bidireccional
    info = relationship("CustomerInfo", back_populates="customer", uselist=False)
    invoices = relationship("Invoice", back_populates="customer")

class CustomerInfo(Base):
    __tablename__ = "customer_info"

    customer_id = Column(Integer, ForeignKey("customers.id"), primary_key=True)
    passport = Column(String(32))

    customer = relationship("Customer", back_populates="info")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    number = Column(String(64))
    date_created = Column(Date)
    date_till = Column(Date)
    total = Column(DECIMAL(19, 4))
    status = Column(Enum("not_paid", "paid", "deleted", "pending"), default="not_paid")
    deleted = Column(Enum("0", "1"), default="0")

    customer = relationship("Customer", back_populates="invoices")
