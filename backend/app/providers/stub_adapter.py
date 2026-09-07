"""
Stub Payment Provider Adapter for testing and architectural validation.
Proves that BharatSHIELD's core intelligence remains strictly provider-independent.
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from backend.app.providers.base import PaymentProvider, CommonTransaction


class StubProviderAdapter(PaymentProvider):
    """
    Mock/Stub Payment Provider for testing provider invariance.
    Emulates an alternative bank or PSP gateway (e.g., HDFC SmartGateway, PayU, PhonePe).
    """

    @property
    def provider_name(self) -> str:
        return "stub"

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: Union[str, List[str], tuple]
    ) -> bool:
        if not signature or not secret:
            return False
        
        candidate_secrets = [secret] if isinstance(secret, str) else list(secret)
        clean_sig = signature.strip()

        for candidate in candidate_secrets:
            if not candidate:
                continue
            if clean_sig == candidate or clean_sig == "STUB_SIG_VALID":
                return True
            expected = hmac.new(candidate.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, clean_sig):
                return True
        return False

    def parse_webhook(
        self,
        payload: Union[Dict[str, Any], bytes],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        if isinstance(payload, bytes):
            data = json.loads(payload.decode("utf-8"))
        else:
            data = payload
        return {
            "event": data.get("event_type", "txn.authorized"),
            "entity": data.get("data", data)
        }

    def normalize(self, raw_data: Dict[str, Any]) -> CommonTransaction:
        entity = raw_data.get("entity", raw_data)
        event_name = raw_data.get("event", "txn.authorized")

        # Alternate gateway convention: txn_ref, billing_amt
        txn_id = entity.get("txn_ref") or entity.get("txn_id") or entity.get("transaction_id") or f"stub_{int(datetime.now(timezone.utc).timestamp())}"
        amount = float(entity.get("billing_amt") or entity.get("amount", 1000.0))
        currency = entity.get("curr", entity.get("currency", "INR")).upper()
        
        # Method mapping: upi_vpa, cc, dc
        raw_method = str(entity.get("channel") or entity.get("payment_type") or entity.get("payment_method", "upi")).lower()
        if "vpa" in raw_method or "upi" in raw_method:
            method = "UPI"
        elif "cc" in raw_method or "card" in raw_method:
            method = "Credit Card"
        else:
            method = raw_method

        created_at_val = entity.get("created_at") or entity.get("timestamp")
        if created_at_val:
            if isinstance(created_at_val, (int, float)):
                txn_time = datetime.fromtimestamp(created_at_val, tz=timezone.utc)
            elif isinstance(created_at_val, datetime):
                txn_time = created_at_val
            else:
                txn_time = datetime.now(timezone.utc)
        else:
            txn_time = datetime.now(timezone.utc)

        metadata = entity.get("signals") or entity.get("custom_fields") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        return CommonTransaction(
            transaction_id=txn_id,
            merchant_id=entity.get("merchant_code") or entity.get("merchant_id", "MER_razorpay_001"),
            customer_id=entity.get("payer_id") or entity.get("customer_id"),
            amount=amount,
            currency=currency,
            payment_method=method,
            timestamp=txn_time,
            device_id=entity.get("device_id") or entity.get("client_device_id", "dev_stub_001"),
            location=entity.get("location") or entity.get("geo_city", "Bengaluru"),
            ip=entity.get("ip") or entity.get("client_ip", "103.21.244.2"),
            provider="stub",
            raw_event_type=event_name,
            metadata=metadata
        )
