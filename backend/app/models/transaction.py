"""
Transaction, Merchant, and User database models.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base

class Merchant(Base):
    __tablename__ = "merchants"
    
    merchant_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    api_key = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    transactions = relationship("Transaction", back_populates="merchant")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    merchant_id = Column(String(64), ForeignKey("merchants.merchant_id"), nullable=True)
    role = Column(String(32), default="analyst")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(64), ForeignKey("merchants.merchant_id"), index=True, nullable=False)
    
    # Financial payload
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    payment_method = Column(String(32), default="UPI")
    status = Column(String(32), default="PENDING")  # ALLOWED, VERIFY_REQUIRED, STEP_UP_REQUIRED, HELD_FOR_REVIEW
    
    # Contextual Telemetry
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    transaction_hour = Column(Integer, nullable=True)
    transaction_day = Column(Integer, nullable=True)
    
    device_id = Column(String(64), index=True, nullable=True)
    device_age_days = Column(Integer, default=0)
    is_new_device = Column(Boolean, default=False)
    device_transaction_count = Column(Integer, default=1)
    failed_attempts = Column(Integer, default=0)
    
    location = Column(String(64), nullable=True)
    is_new_location = Column(Boolean, default=False)
    location_change = Column(Integer, default=0)
    distance_from_previous = Column(Float, default=0.0)
    
    transactions_last_5min = Column(Integer, default=0)
    transactions_last_10min = Column(Integer, default=0)
    transactions_last_1hr = Column(Integer, default=0)
    amount_last_1hr = Column(Float, default=0.0)
    
    avg_transaction_amount = Column(Float, default=0.0)
    amount_deviation = Column(Float, default=1.0)
    historical_frequency = Column(Float, default=1.0)

    # Relationships
    merchant = relationship("Merchant", back_populates="transactions")
    risk_score = relationship("RiskScore", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    risk_factors = relationship("RiskFactor", back_populates="transaction", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="transaction", cascade="all, delete-orphan")

Index("idx_merchant_timestamp", Transaction.merchant_id, Transaction.timestamp)
