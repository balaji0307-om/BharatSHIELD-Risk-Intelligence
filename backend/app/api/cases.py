from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.models.risk_case import RiskCase, RiskScore, RiskFactor
from backend.app.models.transaction import Transaction

router = APIRouter(prefix="/cases", tags=["Case Management"])

class CreateCaseInput(BaseModel):
    transaction_id: str

class UpdateCaseInput(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

@router.post("")
def create_case(payload: CreateCaseInput, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == payload.transaction_id, Transaction.merchant_id == merchant_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    rs = db.query(RiskScore).filter(RiskScore.transaction_id == tx.transaction_id).first()
    priority = "MEDIUM"
    if rs:
        if rs.risk_level == "CRITICAL":
            priority = "CRITICAL"
        elif rs.risk_level == "HIGH":
            priority = "HIGH"
            
    case = RiskCase(
        merchant_id=merchant_id,
        transaction_id=tx.transaction_id,
        title=f"Manual Review required for {tx.transaction_id[:8]}",
        priority=priority,
        status="OPEN"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

@router.get("")
def list_cases(status: Optional[str] = None, priority: Optional[str] = None, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    query = db.query(RiskCase).filter(RiskCase.merchant_id == merchant_id)
    if status:
        query = query.filter(RiskCase.status == status)
    if priority:
        query = query.filter(RiskCase.priority == priority)
    return query.order_by(RiskCase.created_at.desc()).all()

@router.get("/{case_id}")
def get_case(case_id: str, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    case = db.query(RiskCase).filter(RiskCase.case_id == case_id, RiskCase.merchant_id == merchant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    tx = db.query(Transaction).filter(Transaction.transaction_id == case.transaction_id).first()
    factors = db.query(RiskFactor).filter(RiskFactor.transaction_id == case.transaction_id).all()
    
    return {
        "case": case,
        "transaction": tx,
        "risk_factors": factors
    }

@router.put("/{case_id}")
def update_case(case_id: str, payload: UpdateCaseInput, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    case = db.query(RiskCase).filter(RiskCase.case_id == case_id, RiskCase.merchant_id == merchant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if payload.status:
        valid_statuses = ["OPEN", "UNDER_REVIEW", "ESCALATED", "RESOLVED"]
        if payload.status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        case.status = payload.status
        if payload.status == "ESCALATED":
            case.escalated_at = datetime.now(timezone.utc)
        elif payload.status == "RESOLVED":
            case.resolved_at = datetime.now(timezone.utc)
            
    if payload.notes:
        case.notes = payload.notes
    if payload.assigned_to:
        case.assigned_to = payload.assigned_to
        
    db.commit()
    db.refresh(case)
    return case
