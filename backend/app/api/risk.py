"""
Risk API endpoints: ad-hoc assessments, risk cases, and explainability inspections.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.schemas.transaction import TransactionScoreRequest
from backend.app.schemas.risk import RiskAssessment, RiskCaseCreate, RiskCaseOut
from backend.app.services.risk_engine import risk_engine
from backend.app.models.risk_case import RiskCase

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])

@router.post("/assess", response_model=RiskAssessment, summary="Ad-hoc Risk Assessment (Dry Run)")
def assess_risk(payload: TransactionScoreRequest):
    """
    Evaluates risk score and SHAP explanations in real time without writing to the database.
    Ideal for checkout simulators and pre-auth testing.
    """
    raw_dict = payload.model_dump()
    assessment = risk_engine.assess_transaction(raw_dict)
    return assessment

@router.get("/cases", response_model=List[RiskCaseOut], summary="List Risk Cases")
def list_risk_cases(
    merchant_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(RiskCase)
    if merchant_id:
        query = query.filter(RiskCase.merchant_id == merchant_id)
    if status_filter:
        query = query.filter(RiskCase.status == status_filter)
    return query.order_by(RiskCase.created_at.desc()).all()

@router.post("/cases", response_model=RiskCaseOut, summary="Create a Risk Case")
def create_risk_case(
    payload: RiskCaseCreate,
    merchant_id: str = "MER_razorpay_001",
    db: Session = Depends(get_db)
):
    case = RiskCase(
        merchant_id=merchant_id,
        transaction_id=payload.transaction_id,
        title=payload.title,
        priority=payload.priority,
        notes=payload.notes
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case
