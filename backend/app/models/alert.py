"""
Alert model for fraud spikes, rapid velocity anomalies, and threshold events.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, Index
from backend.app.database.connection import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(String(64), primary_key=True, default=lambda: f"ALT-{uuid.uuid4().hex[:8].upper()}")
    merchant_id = Column(String(64), index=True, nullable=False)
    
    alert_type = Column(String(64), nullable=False)  # FRAUD_SPIKE, VELOCITY_ATTACK, UNUSUAL_VOLUME, CRITICAL_TXN
    severity = Column(String(16), nullable=False)    # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    
    # Quantitative telemetry
    spike_percentage = Column(Float, default=0.0)
    suspicious_count = Column(Integer, default=0)
    baseline_volume = Column(Float, default=0.0)
    current_volume = Column(Float, default=0.0)
    
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(128), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

Index("idx_alert_merchant_status", Alert.merchant_id, Alert.is_acknowledged, Alert.created_at)
