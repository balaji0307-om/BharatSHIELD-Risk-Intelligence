"""
Transaction processing service coordinating scoring, persistence, audit trails, and anomaly alerts.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.app.schemas.transaction import TransactionScoreRequest, TransactionScoreResponse
from backend.app.services.risk_engine import risk_engine
from backend.app.services.anomaly_service import AnomalyService
from backend.app.database.repositories import TransactionRepository

anomaly_service = AnomalyService()

class TransactionService:
    @staticmethod
    def process_and_score(db: Session, req: TransactionScoreRequest) -> Dict[str, Any]:
        """
        Receives raw transaction payload:
        1. Evaluates risk via RiskEngine (XGBoost + SHAP).
        2. Determines transactional disposition.
        3. Persists Transaction, RiskScore, RiskFactors.
        4. Writes immutable AuditLog entry.
        5. Checks for velocity / fraud volume spikes.
        """
        raw_dict = req.model_dump()
        txn_id = str(uuid.uuid4())
        raw_dict["transaction_id"] = txn_id
        raw_dict["timestamp"] = datetime.now(timezone.utc)
        
        # 1. Run Risk Engine
        assessment = risk_engine.assess_transaction(raw_dict)
        
        # 2. Map risk band to transaction execution status
        level = assessment["risk_level"]
        if level == "LOW":
            txn_status = "ALLOWED"
        elif level == "MEDIUM":
            txn_status = "VERIFY_REQUIRED"
        elif level == "HIGH":
            txn_status = "STEP_UP_REQUIRED"
        else:
            txn_status = "HOLD_FOR_REVIEW"
            
        raw_dict["status"] = txn_status
        
        # 3. Persist transaction & risk assessment
        txn_row = TransactionRepository.create_transaction(db, raw_dict)
        score_row, factor_rows = TransactionRepository.save_risk_assessment(db, txn_id, assessment)
        
        # 4. Write immutable Audit Trail
        audit_row = TransactionRepository.create_audit_log(
            db, txn_id, req.merchant_id, assessment, raw_dict
        )
        
        # Commit core risk evaluation
        db.commit()
        
        # 5. Background / immediate check for merchant anomaly spikes
        try:
            anomaly_service.evaluate_merchant_spikes(db, req.merchant_id)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Non-blocking anomaly evaluation failed: {exc}")
            
        return {
            "transaction_id": txn_id,
            "merchant_id": req.merchant_id,
            "amount": req.transaction_amount,
            "payment_method": req.payment_method,
            "status": txn_status,
            "fraud_probability": assessment["fraud_probability"],
            "risk_score": assessment["risk_score"],
            "risk_level": assessment["risk_level"],
            "recommended_action": assessment["recommended_action"],
            "risk_factors": assessment["risk_factors"],
            "audit_log_id": audit_row.log_id,
            "timestamp": raw_dict["timestamp"]
        }
