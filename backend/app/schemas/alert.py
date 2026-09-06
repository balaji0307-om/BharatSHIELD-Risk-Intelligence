"""
Pydantic schemas for Alerts and Anomaly detection.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AlertOut(BaseModel):
    alert_id: str
    merchant_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    spike_percentage: float
    suspicious_count: int
    baseline_volume: float
    current_volume: float
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None
