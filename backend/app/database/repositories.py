"""
Repository layer providing clean abstractions for DB operations.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from backend.app.models.transaction import Transaction, Merchant
from backend.app.models.risk_case import RiskScore, RiskFactor, RiskCase, AuditLog
from backend.app.models.alert import Alert

class TransactionRepository:
    @staticmethod
    def create_transaction(db: Session, data: Dict[str, Any]) -> Transaction:
        txn = Transaction(
            transaction_id=data.get("transaction_id"),
            merchant_id=data.get("merchant_id", "MER_razorpay_001"),
            amount=data["transaction_amount"],
            payment_method=data.get("payment_method", "UPI"),
            status=data.get("status", "PENDING"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc)),
            transaction_hour=data.get("transaction_hour"),
            transaction_day=data.get("transaction_day"),
            device_id=data.get("device_id"),
            device_age_days=data.get("device_age_days", 0),
            is_new_device=data.get("is_new_device", False),
            device_transaction_count=data.get("device_transaction_count", 1),
            failed_attempts=data.get("failed_attempts", 0),
            location=data.get("location", "Mumbai"),
            is_new_location=data.get("is_new_location", False),
            location_change=data.get("location_change", 0),
            distance_from_previous=data.get("distance_from_previous", 0.0),
            transactions_last_5min=data.get("transactions_last_5min", 0),
            transactions_last_10min=data.get("transactions_last_10min", 0),
            transactions_last_1hr=data.get("transactions_last_1hr", 0),
            amount_last_1hr=data.get("amount_last_1hr", 0.0),
            avg_transaction_amount=data.get("avg_transaction_amount", data["transaction_amount"]),
            amount_deviation=data.get("amount_deviation", 1.0),
            historical_frequency=data.get("historical_frequency", 1.0)
        )
        db.add(txn)
        db.flush()
        return txn

    @staticmethod
    def save_risk_assessment(
        db: Session, transaction_id: str, assessment: Dict[str, Any]
    ) -> Tuple[RiskScore, List[RiskFactor]]:
        rec = assessment["recommended_action"]
        risk_score_row = RiskScore(
            transaction_id=transaction_id,
            fraud_probability=assessment["fraud_probability"],
            risk_score=assessment["risk_score"],
            risk_level=assessment["risk_level"],
            recommended_action=rec.get("action", "Allow"),
            recommendation_details=json.dumps(rec.get("details", []))
        )
        db.add(risk_score_row)

        factor_rows = []
        for factor in assessment.get("risk_factors", []):
            rf = RiskFactor(
                transaction_id=transaction_id,
                feature=factor.get("feature", "unknown"),
                display_name=factor.get("display_name", "Factor"),
                contribution=float(factor.get("contribution", 0.0)),
                direction=factor.get("direction", "increases_risk"),
                feature_value=str(factor.get("value", ""))
            )
            db.add(rf)
            factor_rows.append(rf)

        db.flush()
        return risk_score_row, factor_rows

    @staticmethod
    def create_audit_log(
        db: Session, transaction_id: str, merchant_id: str, assessment: Dict[str, Any], raw_payload: Dict[str, Any]
    ) -> AuditLog:
        reasons_text = "; ".join([
            f"{f.get('display_name')}: {f.get('direction')} (+{f.get('contribution'):.1f}pts)"
            for f in assessment.get("risk_factors", [])[:4]
        ])
        
        now_utc = datetime.now(timezone.utc)
        log_id = f"AUD-{uuid.uuid4().hex[:12]}"
        audit = AuditLog(
            log_id=log_id,
            transaction_id=transaction_id,
            merchant_id=merchant_id,
            decision_type="TRANSACTION_RISK_EVALUATION",
            risk_score=assessment["risk_score"],
            risk_level=assessment["risk_level"],
            recommended_action=assessment["recommended_action"].get("action", "Allow"),
            reasons_summary=reasons_text or "Standard rule & ML assessment pass.",
            raw_payload=json.dumps(raw_payload, default=str),
            created_at=now_utc
        )
        from backend.app.services.audit_chain_service import AuditChainService
        AuditChainService.append_to_chain(db, audit)
        db.add(audit)
        db.flush()
        return audit

    @staticmethod
    def list_transactions(
        db: Session, merchant_id: Optional[str] = None, risk_level: Optional[str] = None,
        page: int = 1, page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = db.query(Transaction, RiskScore).outerjoin(RiskScore, Transaction.transaction_id == RiskScore.transaction_id)
        
        if merchant_id:
            query = query.filter(Transaction.merchant_id == merchant_id)
        if risk_level:
            query = query.filter(RiskScore.risk_level == risk_level.upper())
            
        total = query.count()
        results = query.order_by(desc(Transaction.timestamp)).offset((page - 1) * page_size).limit(page_size).all()
        
        items = []
        for txn, score in results:
            items.append({
                "transaction_id": txn.transaction_id,
                "merchant_id": txn.merchant_id,
                "amount": txn.amount,
                "payment_method": txn.payment_method,
                "status": txn.status,
                "risk_score": score.risk_score if score else 0,
                "risk_level": score.risk_level if score else "LOW",
                "timestamp": txn.timestamp,
                "location": txn.location,
                "is_new_device": txn.is_new_device
            })
        return items, total

    @staticmethod
    def get_transaction_details(db: Session, transaction_id: str) -> Optional[Dict[str, Any]]:
        txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not txn:
            return None
            
        score = db.query(RiskScore).filter(RiskScore.transaction_id == transaction_id).first()
        factors = db.query(RiskFactor).filter(RiskFactor.transaction_id == transaction_id).order_by(desc(RiskFactor.contribution)).all()
        audit = db.query(AuditLog).filter(AuditLog.transaction_id == transaction_id).order_by(desc(AuditLog.created_at)).first()

        factor_list = [{
            "feature": f.feature,
            "display_name": f.display_name,
            "contribution": f.contribution,
            "direction": f.direction,
            "value": f.feature_value
        } for f in factors]

        rec_details = json.loads(score.recommendation_details) if score and score.recommendation_details else []

        return {
            "transaction": {
                "transaction_id": txn.transaction_id,
                "merchant_id": txn.merchant_id,
                "amount": txn.amount,
                "currency": txn.currency,
                "payment_method": txn.payment_method,
                "status": txn.status,
                "timestamp": txn.timestamp,
                "device_id": txn.device_id,
                "device_age_days": txn.device_age_days,
                "is_new_device": txn.is_new_device,
                "failed_attempts": txn.failed_attempts,
                "location": txn.location,
                "is_new_location": txn.is_new_location,
                "distance_from_previous": txn.distance_from_previous,
                "transactions_last_5min": txn.transactions_last_5min,
                "transactions_last_10min": txn.transactions_last_10min,
                "transactions_last_1hr": txn.transactions_last_1hr,
                "amount_deviation": txn.amount_deviation
            },
            "risk_assessment": {
                "fraud_probability": score.fraud_probability if score else 0.0,
                "risk_score": score.risk_score if score else 0,
                "risk_level": score.risk_level if score else "LOW",
                "recommended_action": {
                    "action": score.recommended_action if score else "Allow",
                    "details": rec_details
                },
                "risk_factors": factor_list
            },
            "audit_log": {
                "log_id": audit.log_id if audit else None,
                "reasons_summary": audit.reasons_summary if audit else "N/A",
                "created_at": audit.created_at if audit else None
            }
        }

    @staticmethod
    def get_related_transactions(db: Session, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Heuristic linking: transactions sharing device_id or close location within 24h.
        """
        source = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not source:
            return []

        time_window_start = source.timestamp - timedelta(hours=24)
        time_window_end = source.timestamp + timedelta(hours=24)

        query = db.query(Transaction, RiskScore).outerjoin(
            RiskScore, Transaction.transaction_id == RiskScore.transaction_id
        ).filter(
            Transaction.transaction_id != transaction_id,
            Transaction.merchant_id == source.merchant_id,
            Transaction.timestamp.between(time_window_start, time_window_end)
        )

        if source.device_id:
            query = query.filter(
                (Transaction.device_id == source.device_id) | 
                (Transaction.location == source.location)
            )
        else:
            query = query.filter(Transaction.location == source.location)

        related = query.order_by(desc(Transaction.timestamp)).limit(5).all()
        items = []
        for t, s in related:
            items.append({
                "transaction_id": t.transaction_id,
                "amount": t.amount,
                "payment_method": t.payment_method,
                "status": t.status,
                "risk_score": s.risk_score if s else 0,
                "risk_level": s.risk_level if s else "LOW",
                "timestamp": t.timestamp,
                "shared_link": "Shared Device" if t.device_id == source.device_id else "Same Location"
            })
        return items

class AnalyticsRepository:
    @staticmethod
    def get_overview_kpis(db: Session, merchant_id: Optional[str] = None) -> Dict[str, Any]:
        txn_query = db.query(Transaction)
        risk_query = db.query(RiskScore)
        alert_query = db.query(Alert)

        if merchant_id:
            txn_query = txn_query.filter(Transaction.merchant_id == merchant_id)
            # Filter risk scores via join
            risk_query = risk_query.join(Transaction, RiskScore.transaction_id == Transaction.transaction_id).filter(Transaction.merchant_id == merchant_id)
            alert_query = alert_query.filter(Alert.merchant_id == merchant_id)

        total_txns = txn_query.count()
        fraud_count = risk_query.filter(RiskScore.risk_score >= 75).count()
        high_risk_count = risk_query.filter(RiskScore.risk_score.between(50, 74)).count()
        critical_alerts_count = alert_query.filter(Alert.severity == "CRITICAL", Alert.is_acknowledged == False).count()
        
        avg_score_res = risk_query.with_entities(func.avg(RiskScore.risk_score)).scalar()
        avg_score = round(float(avg_score_res or 0.0), 1)

        return {
            "total_transactions": total_txns,
            "fraud_detected_count": fraud_count,
            "high_risk_count": high_risk_count,
            "critical_alerts_count": critical_alerts_count,
            "average_risk_score": avg_score,
            "fraud_rate_percentage": round((fraud_count / max(1, total_txns)) * 100, 2)
        }

    @staticmethod
    def get_trends(db: Session, merchant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns 24-hour volume and fraud trend buckets."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=24)
        
        query = db.query(
            Transaction.timestamp,
            RiskScore.risk_score
        ).outerjoin(RiskScore, Transaction.transaction_id == RiskScore.transaction_id).filter(
            Transaction.timestamp >= start
        )
        if merchant_id:
            query = query.filter(Transaction.merchant_id == merchant_id)
            
        rows = query.all()
        
        # Aggregate by hour
        buckets: Dict[str, Dict[str, Any]] = {}
        for h in range(24):
            hour_dt = (start + timedelta(hours=h)).strftime("%H:00")
            buckets[hour_dt] = {"time": hour_dt, "total_transactions": 0, "fraud_count": 0, "avg_risk": 0.0, "scores": []}
            
        for ts, score in rows:
            hour_str = ts.strftime("%H:00")
            if hour_str in buckets:
                buckets[hour_str]["total_transactions"] += 1
                sc = score or 0
                buckets[hour_str]["scores"].append(sc)
                if sc >= 75:
                    buckets[hour_str]["fraud_count"] += 1
                    
        result = []
        for k, v in buckets.items():
            scores = v.pop("scores")
            v["avg_risk"] = round(sum(scores) / len(scores), 1) if scores else 0.0
            result.append(v)
            
        return result

class AlertRepository:
    @staticmethod
    def list_alerts(db: Session, merchant_id: Optional[str] = None) -> List[Alert]:
        query = db.query(Alert)
        if merchant_id:
            query = query.filter(Alert.merchant_id == merchant_id)
        return query.order_by(desc(Alert.created_at)).all()

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, acknowledged_by: str = "risk_analyst") -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.is_acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(alert)
        return alert
