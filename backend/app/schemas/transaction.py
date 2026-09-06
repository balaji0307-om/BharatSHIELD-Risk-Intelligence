"""
Pydantic validation schemas for transaction ingestion, evaluation, and responses.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

class TransactionScoreRequest(BaseModel):
    merchant_id: str = Field(default="MER_razorpay_001", description="Merchant Identifier")
    transaction_amount: float = Field(..., gt=0, description="Gross transaction amount in INR")
    payment_method: str = Field(default="UPI", description="UPI, Credit Card, Debit Card, Net Banking, Wallet")
    
    # Optional or defaultable signals
    transaction_hour: Optional[int] = Field(default=None, ge=0, le=23)
    transaction_day: Optional[int] = Field(default=None, ge=0, le=6)
    
    # Device telemetry
    device_id: Optional[str] = Field(default="dev_mobile_001")
    device_age_days: int = Field(default=30, ge=0)
    failed_attempts: int = Field(default=0, ge=0)
    is_new_device: bool = Field(default=False)
    device_transaction_count: int = Field(default=10, ge=0)
    
    # Velocity signals
    transactions_last_5min: int = Field(default=0, ge=0)
    transactions_last_10min: int = Field(default=0, ge=0)
    transactions_last_1hr: int = Field(default=0, ge=0)
    amount_last_1hr: float = Field(default=0.0, ge=0)
    
    # Location signals
    location: Optional[str] = Field(default="Mumbai")
    is_new_location: bool = Field(default=False)
    location_change: int = Field(default=0, ge=0)
    distance_from_previous: float = Field(default=0.0, ge=0)
    
    # Behavioral baseline
    avg_transaction_amount: Optional[float] = Field(default=None)
    amount_deviation: Optional[float] = Field(default=None)
    historical_frequency: float = Field(default=1.0)

class RiskFactorOut(BaseModel):
    feature: str
    display_name: str
    contribution: float
    direction: str
    value: Any

class RecommendedActionOut(BaseModel):
    action: str
    description: str
    urgency: str
    details: List[str] = []

class TransactionScoreResponse(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    payment_method: str
    status: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    recommended_action: RecommendedActionOut
    risk_factors: List[RiskFactorOut]
    audit_log_id: str
    timestamp: datetime

class TransactionSummary(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    payment_method: str
    status: str
    risk_score: int
    risk_level: str
    timestamp: datetime
    location: Optional[str] = None
    is_new_device: bool = False
    
    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
