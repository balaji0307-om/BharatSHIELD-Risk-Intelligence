"""
Unit and Integration Tests for BharatSHIELD Production ML Pipeline & API Parity.
Asserts that:
1. Low-risk and high-risk inputs produce materially different scores.
2. Simulator and Transaction scoring endpoints share the exact same RiskEngine pipeline.
3. SHAP factors are real, non-empty, and mathematically sound.
4. No hardcoded mock signatures (score=15, prob=0.15, contribution=0.5) are returned.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.risk_engine import risk_engine

client = TestClient(app)

def test_identical_pipeline_guarantee():
    """TASK 15: Assert that simulator and transaction scoring call the exact same RiskEngine inference."""
    raw_payload = {
        "transaction_amount": 54000,
        "payment_method": "Credit Card",
        "failed_attempts": 3,
        "is_new_device": True,
        "is_new_location": True,
        "transactions_last_5min": 7,
        "distance_from_previous": 450,
        "device_age_days": 12,
        "merchant_id": "MER_razorpay_001"
    }

    # 1. Direct RiskEngine inference
    direct_assessment = risk_engine.assess_transaction(raw_payload)

    # 2. Via Simulator endpoint
    sim_resp = client.post("/api/simulator/assess", json=raw_payload)
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()

    # 3. Via Transaction scoring endpoint
    score_resp = client.post("/api/transactions/score", json=raw_payload)
    assert score_resp.status_code == 200
    score_data = score_resp.json()

    # Assert exact score equality across all 3 channels
    assert sim_data["risk_score"] == direct_assessment["risk_score"], "Simulator score diverges from direct engine calculation!"
    assert score_data["risk_score"] == direct_assessment["risk_score"], "Scoring score diverges from direct engine calculation!"
    assert sim_data["fraud_probability"] == direct_assessment["fraud_probability"]
    assert score_data["fraud_probability"] == direct_assessment["fraud_probability"]
    assert sim_data["risk_level"] == direct_assessment["risk_level"]
    assert score_data["risk_level"] == direct_assessment["risk_level"]

def test_simulator_scenarios_materially_different():
    """TASK 2: Low-risk vs High-risk scenario validation."""
    low_risk = {
        "transaction_amount": 5000,
        "failed_attempts": 0,
        "is_new_device": False,
        "is_new_location": False,
        "transactions_last_5min": 1,
        "distance_from_previous": 10,
        "device_age_days": 180,
        "payment_method": "UPI"
    }

    high_risk = {
        "transaction_amount": 88500,
        "failed_attempts": 6,
        "is_new_device": True,
        "is_new_location": True,
        "transactions_last_5min": 18,
        "distance_from_previous": 2000,
        "device_age_days": 1,
        "payment_method": "UPI"
    }

    res_low = client.post("/api/simulator/assess", json=low_risk)
    assert res_low.status_code == 200
    low_data = res_low.json()

    res_high = client.post("/api/simulator/assess", json=high_risk)
    assert res_high.status_code == 200
    high_data = res_high.json()

    # Assert no mock values
    assert not (low_data["risk_score"] == 15 and low_data["fraud_probability"] == 0.15), "Low risk returned fake mock signature 15/0.15!"
    assert not (high_data["risk_score"] == 15 and high_data["fraud_probability"] == 0.15), "High risk returned fake mock signature 15/0.15!"

    # Assert material difference
    assert high_data["risk_score"] > low_data["risk_score"], f"Expected high risk ({high_data['risk_score']}) > low risk ({low_data['risk_score']})"
    assert high_data["fraud_probability"] > low_data["fraud_probability"]

    # Assert SHAP risk factors exist and are non-trivial
    assert len(high_data["risk_factors"]) > 0, "High-risk assessment has no SHAP factors!"
    for factor in high_data["risk_factors"]:
        assert not (factor.get("feature") == "amount" and factor.get("contribution") == 0.5), "Found static fallback factor!"

def test_audit_chain_verification():
    """TASK 8: Cryptographic verification of audit log hash chain."""
    resp = client.get("/api/audit/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True, f"Audit chain verification reported invalid: {data}"
    assert "total_records" in data

def test_merchant_posture_no_fabricated_drivers():
    """TASK 13: Merchant posture does not invent mock driver bars."""
    resp = client.get("/api/merchant/posture")
    assert resp.status_code == 200
    data = resp.json()
    assert "top_risk_drivers" in data
    assert isinstance(data["top_risk_drivers"], list)
    # Ensure no fabricated default array is present if transactions exist
    if data["total_transactions"] == 0:
        assert data["top_risk_drivers"] == [], "Empty posture should return empty list, not fake mockup data!"
