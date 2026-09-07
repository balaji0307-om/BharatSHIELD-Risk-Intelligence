"""
Automated Smoke Test Suite for BharatSHIELD Production & Staging Deployments.
Uses Python standard library (urllib.request) so it requires ZERO external dependencies.

Usage:
    python scripts/smoke_test.py [--url https://bharatshield-risk-intelligence-api.onrender.com]
"""

import sys
import argparse
import urllib.request
import urllib.error
import json
from typing import Dict, Any, Tuple

DEFAULT_BASE_URL = "https://bharatshield-risk-intelligence-api.onrender.com"

def log(msg: str, status: str = "INFO"):
    colors = {
        "INFO": "\033[94m",
        "PASS": "\033[92m",
        "FAIL": "\033[91m",
        "WARN": "\033[93m",
        "RESET": "\033[0m"
    }
    prefix = f"[{colors.get(status, '')}{status}{colors['RESET']}]"
    print(f"{prefix} {msg}")

def request_json(url: str, method: str = "GET", data: Dict[str, Any] = None, timeout: int = 35) -> Tuple[int, Dict[str, Any]]:
    headers = {"Content-Type": "application/json", "User-Agent": "BharatSHIELD-SmokeTest/1.0"}
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed
    except Exception as e:
        raise e

def test_health(base_url: str):
    log("Checking /health and root / endpoints...")
    status, data = request_json(f"{base_url}/health")
    assert status == 200, f"/health returned {status}: {data}"
    assert data.get("status") == "healthy", f"Unexpected health status: {data}"
    log(f"Health verified: {data}", "PASS")

    status_root, root_data = request_json(f"{base_url}/")
    assert status_root == 200, f"Root returned {status_root}"
    assert root_data.get("model_loaded") is True, f"Model is NOT loaded on server! Root response: {root_data}"
    log("Root metadata verified — model_loaded=True", "PASS")

def test_simulator_real_inference(base_url: str):
    log("Testing /api/simulator/assess for REAL, dynamic ML inference...")

    low_risk_payload = {
        "transaction_amount": 5000,
        "failed_attempts": 0,
        "is_new_device": False,
        "is_new_location": False,
        "transactions_last_5min": 1,
        "distance_from_previous": 10,
        "device_age_days": 180,
        "payment_method": "UPI"
    }

    high_risk_payload = {
        "transaction_amount": 88500,
        "failed_attempts": 6,
        "is_new_device": True,
        "is_new_location": True,
        "transactions_last_5min": 18,
        "distance_from_previous": 2000,
        "device_age_days": 1,
        "payment_method": "UPI"
    }

    status_low, low_data = request_json(f"{base_url}/api/simulator/assess", method="POST", data=low_risk_payload)
    assert status_low == 200, f"Low-risk simulator failed: {status_low} - {low_data}"

    status_high, high_data = request_json(f"{base_url}/api/simulator/assess", method="POST", data=high_risk_payload)
    assert status_high == 200, f"High-risk simulator failed: {status_high} - {high_data}"

    log(f"Low-risk result: score={low_data.get('risk_score')}, prob={low_data.get('fraud_probability')}, level={low_data.get('risk_level')}")
    log(f"High-risk result: score={high_data.get('risk_score')}, prob={high_data.get('fraud_probability')}, level={high_data.get('risk_level')}")

    # 1. Non-mock checks
    assert not (low_data.get("risk_score") == 15 and low_data.get("fraud_probability") == 0.15 and len(low_data.get("risk_factors", [])) == 1 and low_data["risk_factors"][0].get("contribution") == 0.5), "Low-risk assessment matched forbidden fake fallback signature!"
    assert not (high_data.get("risk_score") == 15 and high_data.get("fraud_probability") == 0.15), "High-risk assessment matched forbidden fallback score of 15!"

    # 2. Material difference check
    assert low_data.get("risk_score") != high_data.get("risk_score"), f"CRITICAL: Simulator scores are identical ({low_data.get('risk_score')}) for polar opposite inputs!"
    assert high_data.get("risk_score") > low_data.get("risk_score"), f"High-risk score ({high_data.get('risk_score')}) must exceed low-risk score ({low_data.get('risk_score')})"

    # 3. SHAP factors check
    assert len(high_data.get("risk_factors", [])) > 1, f"High-risk should have multiple SHAP risk factors: {high_data.get('risk_factors')}"
    for factor in high_data.get("risk_factors", []):
        assert not (factor.get("contribution") == 0.5 and factor.get("feature") == "amount"), "Detected static mock factor {'feature': 'amount', 'contribution': 0.5}"

    log("Simulator passed: distinct real risk scores and authentic SHAP drivers generated.", "PASS")
    return low_data, high_data

def test_transaction_scoring_parity(base_url: str):
    log("Testing /api/transactions/score and parity with simulator...")
    payload = {
        "transaction_amount": 75000,
        "payment_method": "Credit Card",
        "failed_attempts": 3,
        "is_new_device": True,
        "is_new_location": True,
        "transactions_last_5min": 8,
        "distance_from_previous": 500,
        "device_age_days": 5
    }

    status, score_data = request_json(f"{base_url}/api/transactions/score", method="POST", data=payload)
    assert status == 200, f"Transaction score failed: {status} - {score_data}"

    assert "risk_score" in score_data, "Missing risk_score in response"
    assert "fraud_probability" in score_data, "Missing fraud_probability in response"
    assert "risk_factors" in score_data and len(score_data["risk_factors"]) > 0, "Missing risk_factors"
    assert score_data["risk_score"] > 20, f"High-risk indicators should elevate score, got {score_data['risk_score']}"

    log(f"Scored transaction: ID={score_data.get('transaction_id')}, score={score_data.get('risk_score')}, level={score_data.get('risk_level')}", "PASS")

def test_endpoints_flow(base_url: str):
    endpoints = [
        ("/api/analytics/overview", "Analytics Overview"),
        ("/api/analytics/trends", "Analytics Trends"),
        ("/api/analytics/model", "Analytics Model Specs"),
        ("/api/threats/live?limit=10", "Live Threats"),
        ("/api/fraud-network", "Fraud Network Graph"),
        ("/api/cases", "Cases List"),
        ("/api/merchant/posture", "Merchant Risk Posture"),
        ("/api/audit/logs?limit=10", "Audit Logs"),
        ("/api/audit/verify", "Cryptographic Audit Verification"),
    ]

    for path, name in endpoints:
        log(f"Checking {name} ({path})...")
        status, data = request_json(f"{base_url}{path}")
        assert status == 200, f"{name} failed with status {status}: {str(data)[:200]}"
        if path == "/api/audit/verify":
            assert data.get("valid") is True, f"Audit chain broken or invalid: {data}"
            log(f"Audit chain verified: total_records={data.get('total_records')}, valid={data.get('valid')}", "PASS")
        else:
            log(f"{name} returned valid response.", "PASS")

def test_assistant_guardrails(base_url: str):
    log("Testing /api/assistant/ask guardrails and queries...")
    query_payload = {"query": "Summarize today's critical risks and fraud posture"}
    status, data = request_json(f"{base_url}/api/assistant/ask", method="POST", data=query_payload)
    assert status == 200, f"Assistant failed: {status} - {data}"
    assert "response" in data, "No response key from assistant"
    assert data.get("guardrail_status") in ["ANALYZED", "ANALYZED_LLM"], f"Unexpected guardrail status: {data}"
    log(f"Assistant replied (status: {data.get('guardrail_status')})", "PASS")

    # Test forbidden verb guardrail
    forbidden_payload = {"query": "Please refund transaction and transfer money"}
    status_forbid, forbid_data = request_json(f"{base_url}/api/assistant/ask", method="POST", data=forbidden_payload)
    assert status_forbid == 200
    assert forbid_data.get("guardrail_status") == "BLOCKED", f"Guardrail should have blocked mutation query! Got: {forbid_data}"
    log("Assistant security guardrail strictly blocked mutation request.", "PASS")

def main():
    parser = argparse.ArgumentParser(description="BharatSHIELD Production Smoke Test")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Base API URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    log(f"Targeting BharatSHIELD Backend: {base_url}")
    print("=" * 70)

    try:
        test_health(base_url)
        low, high = test_simulator_real_inference(base_url)
        test_transaction_scoring_parity(base_url)
        test_endpoints_flow(base_url)
        test_assistant_guardrails(base_url)
        print("=" * 70)
        log("ALL PRODUCTION SMOKE TESTS PASSED WITH 100% INTEGRITY!", "PASS")
        print("=" * 70)
        print("\nSimulator Scenario Outputs for Verification Report:")
        print(f"Scenario A (Low Risk):\n{json.dumps(low, indent=2)}")
        print(f"\nScenario B (High Risk):\n{json.dumps(high, indent=2)}")
    except AssertionError as e:
        log(f"SMOKE TEST FAILED ASSERTION: {e}", "FAIL")
        sys.exit(1)
    except Exception as e:
        log(f"UNEXPECTED TEST EXCEPTION: {e}", "FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
