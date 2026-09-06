"""
Pydantic schemas for risk assessment, risk cases, and audit inquiries.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RiskAssessment(BaseModel):
    fraud_probability: float
    risk_score: int
    risk_level: str
    recommended_action: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    base_risk_score: float = 10.0
    total_risk_adjustment: float = 0.0

class RiskCaseCreate(BaseModel):
    transaction_id: str
    title: str
    priority: str = "HIGH"
    notes: Optional[str] = None

class RiskCaseOut(BaseModel):
    case_id: str
    merchant_id: str
    transaction_id: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    log_id: str
    transaction_id: str
    merchant_id: str
    risk_score: int
    risk_level: str
    recommended_action: str
    reasons_summary: str
    created_at: datetime

    class Config:
        from_attributes = True
