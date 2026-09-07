"""
Tests for BharatSHIELD Payment Provider Abstraction Layer (Phase 4).
Verifies:
1. PaymentProvider ABC interface compliance.
2. Razorpay signature verification and secret rotation window.
3. Razorpay and Stub data normalization into CommonTransaction.
4. Core RiskEngine ML pipeline provider-invariance (same event from different PSPs produces identical scores & SHAP).
5. Provider-attributed DB persistence via webhook endpoints.
6. /metrics endpoint observability.
"""

import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.providers.base import PaymentProvider, CommonTransaction
from backend.app.providers.razorpay_adapter import RazorpayAdapter
from backend.app.providers.stub_adapter import StubProviderAdapter
from backend.app.providers.registry import ProviderRegistry
from backend.app.services.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.database.connection import SessionLocal
from backend.app.models.transaction import Transaction

client = TestClient(app)


def test_payment_provider_interface_compliance():
    """Test 1: PaymentProvider ABC cannot be instantiated directly and adapters comply."""
    with pytest.raises(TypeError):
        PaymentProvider()  # type: ignore

    razorpay_adapter = ProviderRegistry.get("razorpay")
    stub_adapter = ProviderRegistry.get("stub")

    assert isinstance(razorpay_adapter, PaymentProvider)
    assert isinstance(stub_adapter, PaymentProvider)
    assert "razorpay" in ProviderRegistry.list_providers()
    assert "stub" in ProviderRegistry.list_providers()


def test_razorpay_signature_verification_and_secret_rotation():
    """Test 2: Verify single secret and zero-downtime dual-secret rotation."""
    adapter = RazorpayAdapter()
    active_secret = "sec_active_2026"
    previous_secret = "sec_retired_2025"
    rotation_secrets = [active_secret, previous_secret]

    raw_payload = b'{"event":"payment.captured","entity":"event"}'

    # Generate signature using active secret
    sig_active = hmac.new(active_secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
    # Generate signature using previous secret
    sig_previous = hmac.new(previous_secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
    # Fake invalid signature
    sig_invalid = "0000000000000000000000000000000000000000000000000000000000000000"

    # Single active secret check
    assert adapter.verify_signature(raw_payload, sig_active, active_secret) is True
    assert adapter.verify_signature(raw_payload, sig_invalid, active_secret) is False

    # Dual secret rotation window check
    assert adapter.verify_signature(raw_payload, sig_active, rotation_secrets) is True
    assert adapter.verify_signature(raw_payload, sig_previous, rotation_secrets) is True
    assert adapter.verify_signature(raw_payload, sig_invalid, rotation_secrets) is False


def test_razorpay_and_stub_normalization():
    """Test 3: Verify normalization of gateway payloads into canonical CommonTransaction."""
    # Razorpay payload (amount in paise: 250000 paise = 2500.0 INR)
    rzp_raw = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_999",
                    "amount": 250000,
                    "currency": "INR",
                    "method": "upi",
                    "vpa": "customer@oksbi",
                    "contact": "+919876543210",
                    "email": "customer@example.com",
                    "created_at": 1772870400,
                    "notes": {
                        "merchant_id": "MER_razorpay_001",
                        "device_id": "dev_rzp_42",
                        "ip_address": "49.36.12.8"
                    }
                }
            }
        }
    }

    rzp_adapter = ProviderRegistry.get("razorpay")
    parsed_rzp = rzp_adapter.parse_webhook(rzp_raw)
    common_rzp = rzp_adapter.normalize(parsed_rzp)

    assert isinstance(common_rzp, CommonTransaction)
    assert common_rzp.provider == "razorpay"
    assert common_rzp.amount == 2500.0
    assert common_rzp.payment_method == "UPI"
    assert common_rzp.device_id == "dev_rzp_42"
    assert common_rzp.merchant_id == "MER_razorpay_001"

    # Stub payload (amount directly in INR: 2500.0)
    stub_raw = {
        "event_type": "transaction.success",
        "data": {
            "txn_id": "stub_txn_12345",
            "amount": 2500.0,
            "currency": "INR",
            "payment_type": "UPI",
            "merchant_code": "MER_razorpay_001",
            "device_id": "dev_stub_42",
            "ip": "49.36.12.8"
        }
    }

    stub_adapter = ProviderRegistry.get("stub")
    parsed_stub = stub_adapter.parse_webhook(stub_raw)
    common_stub = stub_adapter.normalize(parsed_stub)

    assert isinstance(common_stub, CommonTransaction)
    assert common_stub.provider == "stub"
    assert common_stub.amount == 2500.0
    assert common_stub.payment_method == "UPI"
    assert common_stub.device_id == "dev_stub_42"


def test_provider_invariance_through_risk_engine():
    """
    Test 4: Core Architectural Invariance Proof.
    Transactions arriving from Razorpay and StubProvider representing the identical
    underlying economic event produce IDENTICAL risk scores, SHAP explanations,
    and policy recommendations when assessed by RiskEngine.
    """
    signals = {
        "transaction_amount": 42000.0,
        "payment_method": "Credit Card",
        "failed_attempts": 2,
        "is_new_device": True,
        "is_new_location": True,
        "transactions_last_5min": 5,
        "distance_from_previous": 280.0,
        "device_age_days": 15,
        "merchant_id": "MER_razorpay_001"
    }

    # Package as Razorpay webhook
    rzp_raw = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_inv_rzp_1",
                    "amount": int(signals["transaction_amount"] * 100),  # Paise
                    "currency": "INR",
                    "method": "card",
                    "created_at": 1772870400,
                    "notes": signals
                }
            }
        }
    }

    # Package as Stub provider webhook
    stub_raw = {
        "event_type": "transaction.success",
        "data": {
            "txn_id": "pay_inv_stub_1",
            "amount": signals["transaction_amount"],
            "currency": "INR",
            "payment_type": "Credit Card",
            "created_at": 1772870400,
            "merchant_code": signals["merchant_id"],
            "signals": signals
        }
    }

    # Normalize both
    rzp_common = ProviderRegistry.get("razorpay").normalize(
        ProviderRegistry.get("razorpay").parse_webhook(rzp_raw)
    )
    stub_common = ProviderRegistry.get("stub").normalize(
        ProviderRegistry.get("stub").parse_webhook(stub_raw)
    )

    # Assess both through core risk engine
    rzp_assessment = risk_engine.assess_transaction(rzp_common.to_feature_dict())
    stub_assessment = risk_engine.assess_transaction(stub_common.to_feature_dict())

    # Invariance assertions:
    assert rzp_assessment["risk_score"] == stub_assessment["risk_score"]
    assert rzp_assessment["fraud_probability"] == stub_assessment["fraud_probability"]
    assert rzp_assessment["risk_level"] == stub_assessment["risk_level"]
    assert rzp_assessment["recommended_action"]["action"] == stub_assessment["recommended_action"]["action"]

    # SHAP explanations invariance check
    rzp_factors = [f["feature"] for f in rzp_assessment["risk_factors"]]
    stub_factors = [f["feature"] for f in stub_assessment["risk_factors"]]
    assert rzp_factors == stub_factors


def test_webhook_endpoints_e2e():
    """Test 5: E2E Webhook endpoint ingestion, signature verification, and DB provider attribution."""
    # 1. Razorpay Webhook
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    import uuid
    rzp_txn_id = f"pay_live_test_{uuid.uuid4().hex[:8]}"
    rzp_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": rzp_txn_id,
                    "amount": 350000,  # 3500 INR
                    "currency": "INR",
                    "method": "upi",
                    "created_at": 1772870400,
                    "notes": {
                        "merchant_id": "MER_razorpay_001",
                        "failed_attempts": 0,
                        "is_new_device": False,
                        "transactions_last_5min": 1
                    }
                }
            }
        }
    }
    raw_body = json.dumps(rzp_payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    resp = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"x-razorpay-signature": sig, "Content-Type": "application/json"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"].upper() == "PROCESSED"
    assert data["provider"] == "razorpay"
    assert "risk_assessment" in data

    # Verify DB attribution
    db = SessionLocal()
    txn = db.query(Transaction).filter(Transaction.transaction_id == rzp_txn_id).first()
    assert txn is not None
    assert txn.provider == "razorpay"
    assert txn.amount == 3500.0
    db.close()

    # 2. Stub Webhook
    stub_secret = "stub_secret_key"
    stub_txn_id = f"stub_live_test_{uuid.uuid4().hex[:8]}"
    stub_payload = {
        "event_type": "transaction.success",
        "data": {
            "txn_id": stub_txn_id,
            "amount": 12000.0,
            "currency": "INR",
            "payment_type": "UPI",
            "merchant_code": "MER_razorpay_001"
        }
    }
    stub_raw_body = json.dumps(stub_payload).encode("utf-8")
    stub_sig = hmac.new(stub_secret.encode("utf-8"), stub_raw_body, hashlib.sha256).hexdigest()

    resp2 = client.post(
        "/api/webhooks/stub",
        content=stub_raw_body,
        headers={"x-stub-signature": stub_sig, "Content-Type": "application/json"}
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"].upper() == "PROCESSED"
    assert data2["provider"] == "stub"

    # Verify DB attribution for stub
    db = SessionLocal()
    txn2 = db.query(Transaction).filter(Transaction.transaction_id == stub_txn_id).first()
    assert txn2 is not None
    assert txn2.provider == "stub"
    assert txn2.amount == 12000.0
    db.close()

    # 3. Invalid signature test
    resp_invalid = client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"x-razorpay-signature": "invalid_sig_abc", "Content-Type": "application/json"}
    )
    assert resp_invalid.status_code == 401

    # 4. Unknown provider test
    resp_unknown = client.post(
        "/api/webhooks/unknown_psp",
        content=b"{}",
        headers={"Content-Type": "application/json"}
    )
    assert resp_unknown.status_code == 404


def test_metrics_endpoint():
    """Test 6: Expose latency, error rate, model inference status, and provider stats."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    metrics = resp.json()

    assert metrics["status"] == "healthy"
    assert "total_requests" in metrics
    assert "error_rate" in metrics
    assert "avg_latency_ms" in metrics
    assert metrics["model_inference_loaded"] is True
    assert "razorpay" in metrics["registered_providers"]
    assert "stub" in metrics["registered_providers"]
    assert isinstance(metrics["provider_stats"], dict)
