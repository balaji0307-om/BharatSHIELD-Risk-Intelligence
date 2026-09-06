from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.models.transaction import Transaction
from backend.app.models.risk_case import RiskScore, RiskFactor

router = APIRouter(prefix="/threats", tags=["Threat Feed"])

@router.get("/live")
def get_live_threats(limit: int = 20, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    threats = db.query(Transaction, RiskScore).join(RiskScore).filter(
        Transaction.merchant_id == merchant_id,
        RiskScore.risk_score >= 30
    ).order_by(Transaction.timestamp.desc()).limit(limit).all()
    
    results = []
    for tx, rs in threats:
        top_factor = db.query(RiskFactor).filter(RiskFactor.transaction_id == tx.transaction_id).order_by(RiskFactor.contribution.desc()).first()
        results.append({
            "transaction_id": tx.transaction_id[:8],
            "amount": tx.amount,
            "risk_score": rs.risk_score,
            "risk_level": rs.risk_level,
            "top_risk_factor": top_factor.display_name if top_factor else "Unknown",
            "timestamp": tx.timestamp
        })
    return results
