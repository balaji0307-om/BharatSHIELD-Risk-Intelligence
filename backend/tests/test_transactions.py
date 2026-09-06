"""
Tests for Transaction Submission, Risk Engine Execution, and Audit Trail Persistence.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.connection import Base
from backend.app.schemas.transaction import TransactionScoreRequest
from backend.app.services.transaction_service import TransactionService
from backend.app.database.repositories import TransactionRepository
from backend.app.models.transaction import Merchant

# In-memory test SQLite DB
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    # Seed test merchant
    m = Merchant(merchant_id="MER_test_001", name="Test Merchant", api_key="key_test")
    db.add(m)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_score_and_persist_transaction(db_session):
    """Test full transaction scoring pipeline and immutable audit log creation."""
    payload = TransactionScoreRequest(
        merchant_id="MER_test_001",
        transaction_amount=95000.0,
        payment_method="UPI",
        transaction_hour=2,
        device_age_days=1,
        failed_attempts=5,
        transactions_last_5min=12,
        transactions_last_10min=20,
        transactions_last_1hr=35,
        amount_last_1hr=210000.0,
        is_new_device=True,
        is_new_location=True,
        device_transaction_count=1,
        avg_transaction_amount=15000.0,
        location="Delhi",
        distance_from_previous=1800.0
    )
    
    res = TransactionService.process_and_score(db_session, payload)
    
    assert res["transaction_id"] is not None
    assert res["risk_score"] >= 50  # Must flag high risk
    assert res["risk_level"] in ["HIGH", "CRITICAL"]
    assert res["status"] in ["STEP_UP_REQUIRED", "HOLD_FOR_REVIEW"]
    assert len(res["risk_factors"]) > 0
    assert res["audit_log_id"] is not None

    # Verify audit log in database
    details = TransactionRepository.get_transaction_details(db_session, res["transaction_id"])
    assert details is not None
    assert details["transaction"]["amount"] == 95000.0
    assert details["risk_assessment"]["risk_score"] == res["risk_score"]
    assert details["audit_log"]["log_id"] == res["audit_log_id"]
