"""
End-to-End integration test for the full BharatSHIELD pipeline:
Submit transaction -> ML inference -> SHAP explainability -> DB persistence -> Audit log -> Analytics.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from tests.fixtures.sample_transactions import LEGITIMATE_TRANSACTION, CRITICAL_FRAUD_TRANSACTION

client = TestClient(app)

def test_health_and_root_endpoints():
    """Verify system health and metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert data["model_loaded"] is True
    assert data["explainer_loaded"] is True

def test_legitimate_transaction_flow():
    """Verify straight-through processing for legitimate transaction."""
    res = client.post("/api/transactions/score", json=LEGITIMATE_TRANSACTION)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] < 50
    assert data["status"] in ["ALLOWED", "VERIFY_REQUIRED"]
    assert "Allow" in data["recommended_action"]["action"] or "Verify" in data["recommended_action"]["action"]
    assert "audit_log_id" in data

def test_critical_fraud_transaction_flow():
    """Verify high-risk detection, SHAP attribution, and audit logging."""
    res = client.post("/api/transactions/score", json=CRITICAL_FRAUD_TRANSACTION)
    assert res.status_code == 200
    data = res.json()
    
    assert data["risk_score"] >= 75
    assert data["risk_level"] == "CRITICAL"
    assert data["status"] == "HOLD_FOR_REVIEW"
    assert "Hold" in data["recommended_action"]["action"]
    assert len(data["risk_factors"]) > 0

    # Verify transaction can be retrieved via deep dive
    txn_id = data["transaction_id"]
    detail_res = client.get(f"/api/transactions/{txn_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["transaction"]["transaction_id"] == txn_id
    assert detail_data["risk_assessment"]["risk_score"] == data["risk_score"]
    assert detail_data["audit_log"]["log_id"] == data["audit_log_id"]

def test_model_analytics_endpoint():
    """Verify model performance metrics are returned directly from the trained artifact."""
    res = client.get("/api/analytics/model")
    assert res.status_code == 200
    data = res.json()
    assert data["model_name"] == "xgboost"
    assert "evaluation_metrics" in data
    assert data["evaluation_metrics"]["f1_score"] is not None
    assert "model_comparison" in data
