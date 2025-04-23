from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, DECIMAL, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

# Tablas relacionadas a Splynx
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))

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


# Tablas locales para persistir consultas
class BancoEstadoInvoice(Base):
    __tablename__ = "be_invoices"

    id_boleta = Column(Integer, primary_key=True, autoincrement=False)
    numero_orden = Column(String(255), ForeignKey("be_data.numero_orden"), primary_key=True)
    numero_boleta = Column(String(255), nullable=False)
    monto = Column(Integer, nullable=False)
    payment_id = Column(Integer, nullable=True)
    transaction_id = Column(Integer, nullable=True)
    vencido = Column(Boolean, nullable=True)


class BancoEstadoData(Base):
    __tablename__ = "be_data"

    numero_orden = Column(String(255), primary_key=True)
    monto_deuda_total = Column(Integer, nullable=False)
    monto_deuda_vencida = Column(Integer, nullable=False)
    fecha_pago = Column(Date, nullable=True)
    fecha_contable = Column(Date, nullable=True)
    canal_pago = Column(String(100), nullable=True)
    estado = Column(String(20), nullable=True)
    monto_pagado = Column(Integer, nullable=True)
    socio = Column(String(10), nullable=True, default="Nx", server_default="Nx")

    invoices = relationship("BancoEstadoInvoice", backref="orden", cascade="all, delete-orphan")

