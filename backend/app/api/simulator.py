"""
Risk Simulator API: What-if analysis using the production ML pipeline.
Does NOT write to the database or audit trail — purely read-only inference.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.core.security import get_current_merchant_id
from backend.app.services.risk_engine import risk_engine

logger = logging.getLogger(__name__)

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
    """
    Runs the full production inference pipeline (feature engineering → scaler →
    XGBoost predict_proba → SHAP explanation → recommendation) without any
    database writes.  Shares the exact same RiskEngine.assess_transaction()
    code path as POST /api/transactions/score.
    """
    raw_input = payload.model_dump()
    raw_input["transaction_id"] = "SIM_WHAT_IF"
    raw_input["merchant_id"] = merchant_id

    try:
        assessment = risk_engine.assess_transaction(raw_input)
    except Exception as exc:
        logger.error(f"Simulator inference failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Risk engine inference failed: {str(exc)}"
        )

    return {
        "fraud_probability": assessment["fraud_probability"],
        "risk_score": assessment["risk_score"],
        "risk_level": assessment["risk_level"],
        "recommended_action": assessment["recommended_action"],
        "risk_factors": assessment["risk_factors"],
        "base_risk_score": assessment["base_risk_score"],
        "total_risk_adjustment": assessment["total_risk_adjustment"],
        "disclaimer": "Simulation only — does not affect actual transactions or audit trail"
    }
