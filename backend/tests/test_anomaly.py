"""
Tests for Fraud Spike Detection and Volume Anomaly Service.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.connection import Base
from backend.app.models.transaction import Transaction, Merchant
from backend.app.models.risk_case import RiskScore
from backend.app.services.anomaly_service import AnomalyService

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    m = Merchant(merchant_id="MER_anomaly_001", name="Anomaly Test Merchant", api_key="key_anomaly")
    db.add(m)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_fraud_spike_trigger(db_session):
    """Test that a burst of high-risk transactions triggers an anomaly alert."""
    anomaly_svc = AnomalyService(zscore_threshold=1.5, suspicious_ratio_threshold=0.20)
    merchant_id = "MER_anomaly_001"
    now = datetime.now(timezone.utc)
    
    # 1. Seed historical baseline over 24h (23 low risk transactions)
    for i in range(23):
        t = Transaction(
            transaction_id=f"base_{i}",
            merchant_id=merchant_id,
            amount=500.0,
            timestamp=now - timedelta(hours=i + 1),
            status="ALLOWED"
        )
        s = RiskScore(
            transaction_id=f"base_{i}",
            fraud_probability=0.02,
            risk_score=10,
            risk_level="LOW",
            recommended_action="Allow"
        )
        db_session.add(t)
        db_session.add(s)
    db_session.commit()

    # 2. Inject fraud spike in current 60m window (5 critical transactions out of 6)
    for i in range(5):
        t = Transaction(
            transaction_id=f"spike_{i}",
            merchant_id=merchant_id,
            amount=85000.0,
            timestamp=now - timedelta(minutes=5 * i),
            status="HOLD_FOR_REVIEW"
        )
        s = RiskScore(
            transaction_id=f"spike_{i}",
            fraud_probability=0.92,
            risk_score=90,
            risk_level="CRITICAL",
            recommended_action="Hold for Review"
        )
        db_session.add(t)
        db_session.add(s)
    db_session.commit()

    # 3. Evaluate spikes
    alert = anomaly_svc.evaluate_merchant_spikes(db_session, merchant_id, window_minutes=60)
    
    assert alert is not None
    assert alert.alert_type == "FRAUD_SPIKE"
    assert alert.severity in ["HIGH", "CRITICAL"]
    assert alert.suspicious_count >= 5
