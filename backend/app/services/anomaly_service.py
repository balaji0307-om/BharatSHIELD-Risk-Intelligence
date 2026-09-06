"""
Anomaly detection service: monitors rolling window volume and fraud spike ratios.
Generates alerts when transaction bursts or high-risk ratios breach baselines.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.transaction import Transaction
from backend.app.models.risk_case import RiskScore
from backend.app.models.alert import Alert

class AnomalyService:
    def __init__(self, zscore_threshold: float = 2.0, suspicious_ratio_threshold: float = 0.20):
        self.zscore_threshold = zscore_threshold
        self.suspicious_ratio_threshold = suspicious_ratio_threshold

    def evaluate_merchant_spikes(
        self, db: Session, merchant_id: str, window_minutes: int = 60
    ) -> Optional[Alert]:
        """
        Evaluates immediate transaction volume and high-risk ratio against historical baseline.
        If a spike is detected, persists and returns an Alert model.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        baseline_start = now - timedelta(hours=24)
        
        # 1. Recent window stats
        recent_txns = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp >= window_start
        ).all()
        recent_count = len(recent_txns)
        
        if recent_count == 0:
            return None
            
        recent_ids = [t.transaction_id for t in recent_txns]
        recent_suspicious = db.query(RiskScore).filter(
            RiskScore.transaction_id.in_(recent_ids),
            RiskScore.risk_score >= 50  # HIGH or CRITICAL
        ).count()
        
        suspicious_ratio = (recent_suspicious / recent_count) if recent_count > 0 else 0.0
        
        # 2. Historical baseline (last 24h, normalized to window size)
        total_24h_count = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp >= baseline_start,
            Transaction.timestamp < window_start
        ).count()
        
        # Expected count per 1-hour window over 23 hours
        expected_window_count = max(1.0, total_24h_count / 23.0)
        volume_increase = (recent_count - expected_window_count) / expected_window_count
        
        spike_detected = False
        alert_type = "UNUSUAL_VOLUME"
        severity = "MEDIUM"
        title = ""
        description = ""
        
        # Condition A: Fraud ratio spike
        if suspicious_ratio >= self.suspicious_ratio_threshold and recent_suspicious >= 3:
            spike_detected = True
            alert_type = "FRAUD_SPIKE"
            severity = "CRITICAL" if suspicious_ratio > 0.40 else "HIGH"
            title = f"Fraud Spike Detected: {suspicious_ratio*100:.1f}% Suspicious Transactions"
            description = (
                f"{recent_suspicious} out of {recent_count} transactions in the last {window_minutes} minutes "
                f"exceed high-risk thresholds (ratio: {suspicious_ratio*100:.1f}% vs baseline < 5%)."
            )
        # Condition B: High velocity burst
        elif volume_increase >= 2.0 and recent_count >= 10:
            spike_detected = True
            alert_type = "VELOCITY_ATTACK"
            severity = "HIGH"
            title = f"Abnormal Volume Surge: +{volume_increase*100:.1f}% over Baseline"
            description = (
                f"Merchant volume reached {recent_count} transactions/hr compared to the baseline of "
                f"{expected_window_count:.1f}/hr."
            )
            
        if spike_detected:
            # Check if an active unacknowledged alert already exists in the last 30 minutes
            recent_alert = db.query(Alert).filter(
                Alert.merchant_id == merchant_id,
                Alert.alert_type == alert_type,
                Alert.is_acknowledged == False,
                Alert.created_at >= now - timedelta(minutes=30)
            ).first()
            
            if recent_alert:
                return recent_alert
                
            alert = Alert(
                merchant_id=merchant_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                spike_percentage=float(volume_increase * 100),
                suspicious_count=recent_suspicious,
                baseline_volume=float(expected_window_count),
                current_volume=float(recent_count),
                is_acknowledged=False
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            return alert
            
        return None
