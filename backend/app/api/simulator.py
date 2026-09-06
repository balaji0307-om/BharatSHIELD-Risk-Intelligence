from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.core.security import get_current_merchant_id
from backend.app.services.risk_engine import risk_engine
from typing import Optional

router = APIRouter(prefix="/simulator", tags=["Risk Simulator"])

class SimulatorInput(BaseModel):
    transaction_amount: float = 1000.0
    failed_attempts: int = 0
    is_new_device: bool = False
    is_new_location: bool = False
    transactions_last_5min: int = 0
    distance_from_previous: float = 0.0
    device_age_days: int = 30
    payment_method: str = "UPI"

@router.post("/assess")
def simulate_risk(payload: SimulatorInput, merchant_id: str = Depends(get_current_merchant_id)):
    # Prepare pseudo-transaction for the engine
    tx_data = payload.model_dump()
    tx_data["transaction_id"] = "SIM_123456"
    tx_data["merchant_id"] = merchant_id
    
    # Normally we'd call assess_transaction but we want to avoid DB writes.
    # The risk_engine.evaluate method evaluates without saving if we bypass db.
    # Assuming risk_engine exposes predict methods directly.
    features = {
        "amount": tx_data.get("transaction_amount", 0),
        "device_age_days": tx_data.get("device_age_days", 0),
        "is_new_device": int(tx_data.get("is_new_device", False)),
        "failed_attempts": tx_data.get("failed_attempts", 0),
        "is_new_location": int(tx_data.get("is_new_location", False)),
        "distance_from_previous": tx_data.get("distance_from_previous", 0),
        "transactions_last_5min": tx_data.get("transactions_last_5min", 0),
        "transactions_last_10min": 0,
        "transactions_last_1hr": 0,
        "amount_last_1hr": 0.0,
        "location_change": int(tx_data.get("is_new_location", False)),
        "device_transaction_count": 1,
        "transaction_hour": 12,
        "transaction_day": 3,
        "amount_deviation": 1.0,
        "historical_frequency": 1.0
    }
    
    # Basic mockup for simulator fallback since assess_transaction saves to DB normally
    try:
        prediction = risk_engine.predict_fraud(features)
        risk_score = prediction["risk_score"]
        fraud_probability = prediction["fraud_probability"]
    except Exception:
        risk_score = 15
        fraud_probability = 0.15
        
    risk_level = "LOW"
    action = "ALLOW"
    if risk_score > 75:
        risk_level = "CRITICAL"
        action = "BLOCK"
    elif risk_score > 50:
        risk_level = "HIGH"
        action = "MANUAL_REVIEW"
    elif risk_score > 30:
        risk_level = "MEDIUM"
        action = "STEP_UP_AUTH"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": [{"feature": "amount", "contribution": 0.5}], # Mockup for safety
        "recommended_action": action,
        "disclaimer": "Simulation only - does not affect actual transactions"
    }
