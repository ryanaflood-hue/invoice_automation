from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import os

# Use DATABASE_URL if available (Vercel/Heroku), else local SQLite
# Vercel Postgres uses POSTGRES_URL by default
database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or "sqlite:///invoice_app_v2.db"

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    property_city = Column(String, nullable=True)
    property_state = Column(String, nullable=True)
    property_zip = Column(String, nullable=True)
    rate = Column(Float, nullable=False)  # amount per period
    cadence = Column(String, nullable=False)  # "monthly", "quarterly", "yearly"
    fee_type = Column(String, nullable=True, default="Management Fee")
    fee_2_type = Column(String, nullable=True)
    fee_2_rate = Column(Float, nullable=True)
    fee_3_type = Column(String, nullable=True)
    fee_3_rate = Column(Float, nullable=True)
    additional_fee_desc = Column(String, nullable=True)
    additional_fee_amount = Column(Float, nullable=True)
    next_bill_date = Column(Date, nullable=False)

    properties = relationship("Property", back_populates="customer", cascade="all, delete-orphan")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    fee_amount = Column(Float, nullable=True)
    is_primary = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="properties")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    invoice_date = Column(Date, nullable=False)
    period_label = Column(String, nullable=False)   # e.g. "3rd quarter 2025"
    amount = Column(Float, nullable=False)
    file_path = Column(String, nullable=False)      # path to generated docx
    email_subject = Column(String, nullable=False)
    email_body = Column(Text, nullable=False)
    
    # Multiple fees
    fee_2_type = Column(String, nullable=True)
    fee_2_amount = Column(Float, nullable=True)
    fee_3_type = Column(String, nullable=True)
    fee_3_amount = Column(Float, nullable=True)
    additional_fee_desc = Column(String, nullable=True)
    additional_fee_amount = Column(Float, nullable=True)
    status = Column(String, default="Unpaid")

class FeeType(Base):
    __tablename__ = "fee_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
