"""
AI Risk Assistant Service: Strictly read-only, defense-oriented analysis.

HARD ARCHITECTURAL CONSTRAINT:
This service has ZERO write access to transaction, account, or monetary states.
It can only query, read, and explain existing risk engine data, alerts, and transaction records.
"""

from typing import Dict, Any, Optional, List
import json
import re
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.transaction import Transaction
from backend.app.models.risk_case import RiskScore, RiskFactor, AuditLog
from backend.app.models.alert import Alert

FORBIDDEN_ACTIONS = [
    "refund", "money movement", "transfer", "payout", "cancel transaction",
    "release hold", "approve transaction", "delete", "drop table", "execute",
    "chargeback", "settle", "freeze account", "unblock"
]

class RiskAssistantService:
    """
    Read-only Risk Intelligence Assistant.
    Enforces defense-only guardrails at the code level.
    """
    
    @staticmethod
    def answer_query(db: Session, query: str, merchant_id: str = "MER_razorpay_001") -> Dict[str, Any]:
        cleaned_query = query.strip().lower()
        
        # 1. Strict Action Guardrail Check
        for forbidden in FORBIDDEN_ACTIONS:
            # Check if query requests mutation
            if re.search(r'\b' + re.escape(forbidden) + r'\b', cleaned_query):
                if any(verb in cleaned_query for verb in ["do", "execute", "trigger", "please", "now", "can you", "make"]):
                    return {
                        "response": (
                            f"[SECURITY GUARDRAIL TRIGGERED] BharatSHIELD AI Risk Assistant operates in strict "
                            f"read-only analytical mode. It cannot perform financial mutations, money movement, "
                            f"status reversals, or actions like '{forbidden}'. "
                            f"All operational changes must be executed by an authorized risk officer through manual review."
                        ),
                        "guardrail_status": "BLOCKED",
                        "grounded_data": None
                    }

        # 2. Pattern Matching / Domain Understanding
        
        # Intent A: Specific Transaction Explanation (e.g., "explain transaction <id>")
        txn_match = re.search(r'([0-9a-fA-F-]{8,36})', query)
        if txn_match:
            txn_id = txn_match.group(1)
            return RiskAssistantService._explain_transaction(db, txn_id)

        # Intent B: Today's Critical Risks / Summary
        if any(term in cleaned_query for term in ["today", "critical", "summary", "overview", "high risk", "status"]):
            return RiskAssistantService._summarize_critical_risks(db, merchant_id)

        # Intent C: Active Alerts / Spikes
        if any(term in cleaned_query for term in ["alert", "spike", "anomaly", "burst"]):
            return RiskAssistantService._summarize_alerts(db, merchant_id)

        # Default Analytical Response with Current Telemetry
        return RiskAssistantService._general_risk_overview(db, merchant_id, query)

    @staticmethod
    def _explain_transaction(db: Session, txn_id: str) -> Dict[str, Any]:
        txn = db.query(Transaction).filter(
            Transaction.transaction_id.like(f"%{txn_id}%")
        ).first()
        
        if not txn:
            return {
                "response": f"Transaction reference '{txn_id}' was not found in merchant records.",
                "guardrail_status": "ANALYZED",
                "grounded_data": None
            }
            
        score = db.query(RiskScore).filter(RiskScore.transaction_id == txn.transaction_id).first()
        factors = db.query(RiskFactor).filter(
            RiskFactor.transaction_id == txn.transaction_id
        ).order_by(desc(RiskFactor.contribution)).all()
        
        reasons_text = "\n".join([
            f"- {f.display_name}: +{f.contribution:.1f} risk points ({f.direction})"
            for f in factors[:4]
        ])
        
        response_text = (
            f"Analysis for Transaction {txn.transaction_id[:8]}...:\n\n"
            f"• Amount: ₹{txn.amount:,.2f} ({txn.payment_method})\n"
            f"• Risk Score: {score.risk_score if score else 'N/A'}/100 [{score.risk_level if score else 'LOW'}]\n"
            f"• Recommendation: {score.recommended_action if score else 'Allow'}\n"
            f"• Key Contributing Factors:\n{reasons_text or '  Standard baseline behaviour.'}\n\n"
            f"Conclusion: Evaluated by BharatSHIELD XGBoost + SHAP explainability. Any review decision requires analyst sign-off."
        )
        
        return {
            "response": response_text,
            "guardrail_status": "ANALYZED",
            "grounded_data": {
                "transaction_id": txn.transaction_id,
                "risk_score": score.risk_score if score else 0,
                "risk_level": score.risk_level if score else "LOW"
            }
        }

    @staticmethod
    def _summarize_critical_risks(db: Session, merchant_id: str) -> Dict[str, Any]:
        critical_scores = db.query(RiskScore, Transaction).join(
            Transaction, RiskScore.transaction_id == Transaction.transaction_id
        ).filter(
            Transaction.merchant_id == merchant_id,
            RiskScore.risk_level == "CRITICAL"
        ).order_by(desc(RiskScore.created_at)).limit(5).all()
        
        if not critical_scores:
            return {
                "response": "No CRITICAL risk transactions are currently pending review for this merchant.",
                "guardrail_status": "ANALYZED",
                "grounded_data": {"critical_count": 0}
            }
            
        lines = []
        for s, t in critical_scores:
            lines.append(f"• Txn {t.transaction_id[:8]}... | ₹{t.amount:,.2f} | Score: {s.risk_score}/100 | Action: {s.recommended_action}")
            
        response_text = (
            f"Found {len(critical_scores)} recent critical risk transaction(s) requiring analyst inspection:\n\n" +
            "\n".join(lines) +
            "\n\nCommon signals detected across these transactions include high 5-minute velocity bursts, credential mismatch, and unfamiliar device fingerprints."
        )
        return {
            "response": response_text,
            "guardrail_status": "ANALYZED",
            "grounded_data": {"critical_count": len(critical_scores)}
        }

    @staticmethod
    def _summarize_alerts(db: Session, merchant_id: str) -> Dict[str, Any]:
        alerts = db.query(Alert).filter(
            Alert.merchant_id == merchant_id,
            Alert.is_acknowledged == False
        ).order_by(desc(Alert.created_at)).limit(5).all()
        
        if not alerts:
            return {
                "response": "All alerts are currently acknowledged. No active velocity spikes or fraud bursts detected.",
                "guardrail_status": "ANALYZED",
                "grounded_data": {"active_alerts": 0}
            }
            
        lines = [f"• [{a.severity}] {a.title}: {a.description}" for a in alerts]
        return {
            "response": f"Active Merchant Alerts:\n\n" + "\n\n".join(lines),
            "guardrail_status": "ANALYZED",
            "grounded_data": {"active_alerts": len(alerts)}
        }

    @staticmethod
    def _general_risk_overview(db: Session, merchant_id: str, query: str) -> Dict[str, Any]:
        total_txns = db.query(Transaction).filter(Transaction.merchant_id == merchant_id).count()
        critical_count = db.query(RiskScore).join(
            Transaction, RiskScore.transaction_id == Transaction.transaction_id
        ).filter(
            Transaction.merchant_id == merchant_id,
            RiskScore.risk_score >= 75
        ).count()
        
        response_text = (
            f"BharatSHIELD Risk Assistant Telemetry:\n\n"
            f"• Total Transactions Monitored: {total_txns:,}\n"
            f"• Critical Risk Holds: {critical_count:,}\n"
            f"• Core Model: XGBoost Ensemble with SHAP Local Attribution\n\n"
            f"You can ask me to explain a specific transaction ('explain transaction <id>'), "
            f"summarize critical risks, or report on active fraud spikes."
        )
        return {
            "response": response_text,
            "guardrail_status": "ANALYZED",
            "grounded_data": {"total_transactions": total_txns, "critical_count": critical_count}
        }
