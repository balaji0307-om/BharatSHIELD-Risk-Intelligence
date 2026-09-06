"""
Database models for Risk Scores, Risk Factors, Risk Cases, and Immutable Audit Logs.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), unique=True, index=True, nullable=False)
    
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0 to 100
    risk_level = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    recommended_action = Column(String(64), nullable=False)
    recommendation_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    transaction = relationship("Transaction", back_populates="risk_score")

class RiskFactor(Base):
    __tablename__ = "risk_factors"
    
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    
    feature = Column(String(64), nullable=False)
    display_name = Column(String(128), nullable=False)
    contribution = Column(Float, nullable=False)
    direction = Column(String(32), default="increases_risk")
    feature_value = Column(String(128), nullable=True)
    
    transaction = relationship("Transaction", back_populates="risk_factors")

class RiskCase(Base):
    __tablename__ = "risk_cases"
    
    case_id = Column(String(64), primary_key=True, default=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}")
    merchant_id = Column(String(64), index=True, nullable=False)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False)
    
    title = Column(String(256), nullable=False)
    status = Column(String(32), default="OPEN")  # OPEN, UNDER_REVIEW, RESOLVED_BLOCKED, RESOLVED_APPROVED
    priority = Column(String(16), default="HIGH")  # MEDIUM, HIGH, CRITICAL
    assigned_to = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    
    escalated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    """
    Immutable audit log storing exact decision reasoning and payload.
    Any risk decision can be reconstructed later.
    """
    __tablename__ = "audit_logs"
    
    log_id = Column(String(64), primary_key=True, default=lambda: f"AUD-{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    merchant_id = Column(String(64), index=True, nullable=False)
    
    decision_type = Column(String(64), default="RISK_EVALUATION")
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(16), nullable=False)
    recommended_action = Column(String(64), nullable=False)
    
    # Serialized JSON representations
    reasons_summary = Column(Text, nullable=False)
    raw_payload = Column(Text, nullable=False)
    
    hash = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    transaction = relationship("Transaction", back_populates="audit_logs")

Index("idx_audit_merchant_time", AuditLog.merchant_id, AuditLog.created_at)
