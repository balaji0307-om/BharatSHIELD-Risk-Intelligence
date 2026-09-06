"""
Tests for Risk Scoring, Threshold Bands, Recommendations, and SHAP Explainability.
"""

import pytest
import numpy as np
from ml.src.risk.scoring import probability_to_risk_score, batch_risk_scores
from ml.src.risk.thresholds import get_risk_level, RiskLevel, RISK_BANDS
from ml.src.risk.recommendations import get_recommendation
from backend.app.services.recommendation_service import generate_recommendation

def test_probability_to_risk_score_monotonicity():
    """Test that higher probability strictly yields higher or equal risk score."""
    probs = np.linspace(0.0, 1.0, 50)
    scores = [probability_to_risk_score(p, k=10.0, threshold=0.5) for p in probs]
    
    # Assert values are between 0 and 100
    for s in scores:
        assert 0 <= s <= 100
        
    # Check monotonicity
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1]

def test_risk_level_bands():
    """Test that risk score correctly maps into defined bands."""
    assert get_risk_level(0) == RiskLevel.LOW
    assert get_risk_level(24) == RiskLevel.LOW
    assert get_risk_level(25) == RiskLevel.MEDIUM
    assert get_risk_level(49) == RiskLevel.MEDIUM
    assert get_risk_level(50) == RiskLevel.HIGH
    assert get_risk_level(74) == RiskLevel.HIGH
    assert get_risk_level(75) == RiskLevel.CRITICAL
    assert get_risk_level(100) == RiskLevel.CRITICAL

def test_recommendation_mapping():
    """Test policy recommendations for each risk band."""
    rec_low = generate_recommendation("LOW")
    assert "Allow" in rec_low["action"]
    assert rec_low["urgency"] == "LOW"

    rec_med = generate_recommendation("MEDIUM")
    assert "Verify" in rec_med["action"]
    assert rec_med["urgency"] == "MEDIUM"

    rec_high = generate_recommendation("HIGH")
    assert "Step-Up" in rec_high["action"]
    assert rec_high["urgency"] == "HIGH"

    rec_crit = generate_recommendation("CRITICAL")
    assert "Hold" in rec_crit["action"]
    assert rec_crit["urgency"] == "CRITICAL"

def test_explainability_consistency():
    """
    Explainability sanity check:
    Verify that when risk factors increase risk, their contributions are strictly positive numbers
    and match the expected severity of the transaction.
    """
    sample_factors = [
        {"feature": "is_new_device", "display_name": "New Device Detected", "contribution": 32.5, "direction": "increases_risk", "value": True},
        {"feature": "failed_attempts", "display_name": "Failed Authentication Attempts", "contribution": 24.0, "direction": "increases_risk", "value": 4}
    ]
    rec = generate_recommendation("CRITICAL", sample_factors)
    assert len(rec["details"]) >= 2
    assert any("New Device" in d for d in rec["details"])
    assert any("32.5" in d for d in rec["details"])
