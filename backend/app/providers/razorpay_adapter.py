"""
Razorpay Payment Provider Adapter.
Converts Razorpay Webhooks and Events into BharatSHIELD CommonTransaction.
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from backend.app.providers.base import PaymentProvider, CommonTransaction


class RazorpayAdapter(PaymentProvider):
    """
    Production-grade Razorpay Gateway Adapter.
    Handles HMAC-SHA256 signature verification with secret rotation,
    webhook ingestion, paise-to-rupee normalization, and metadata extraction.
    """

    @property
    def provider_name(self) -> str:
        return "razorpay"

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: Union[str, List[str], tuple]
    ) -> bool:
        if not signature or not secret:
            return False
        
        # Support secret rotation (window where both current and previous keys are valid)
        candidate_secrets = [secret] if isinstance(secret, str) else list(secret)
        
        clean_sig = signature.strip()
        for candidate in candidate_secrets:
            if not candidate:
                continue
            expected = hmac.new(
                candidate.encode("utf-8"),
                payload,
                hashlib.sha256
            ).hexdigest()
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

        event_name = data.get("event", "payment.authorized")
        entity_payload = data.get("payload", {})
        
        # Razorpay nests payments under payload.payment.entity or payload.order.entity
        payment_entity = (
            entity_payload.get("payment", {}).get("entity", {})
            or entity_payload.get("order", {}).get("entity", {})
            or data
        )

        return {
            "event": event_name,
            "entity": payment_entity,
            "account_id": data.get("account_id"),
            "created_at": data.get("created_at")
        }

    def normalize(self, raw_data: Dict[str, Any]) -> CommonTransaction:
        entity = raw_data.get("entity", raw_data)
        event_name = raw_data.get("event", entity.get("event", "payment.authorized"))
        
        # Financial parsing: Razorpay INR amounts are in paise (1 INR = 100 paise)
        raw_amount = entity.get("amount", 0.0)
        currency = entity.get("currency", "INR").upper()
        if currency == "INR" and raw_amount >= 100 and isinstance(raw_amount, (int, float)) and entity.get("amount_in_paise", True) is not False:
            normalized_amount = float(raw_amount) / 100.0
        else:
            normalized_amount = float(raw_amount)

        # Timestamps
        created_at_ts = entity.get("created_at")
        if created_at_ts and isinstance(created_at_ts, (int, float)):
            txn_time = datetime.fromtimestamp(created_at_ts, tz=timezone.utc)
        else:
            txn_time = datetime.now(timezone.utc)

        # Notes and telemetry
        notes = entity.get("notes", {}) or {}
        device_id = (
            notes.get("device_id")
            or entity.get("device_id")
            or "dev_rzp_default"
        )
        location = notes.get("location") or entity.get("location") or "Mumbai"
        ip = entity.get("ip") or notes.get("ip") or entity.get("client_ip")

        merchant_id = notes.get("merchant_id") or entity.get("merchant_id", "MER_razorpay_001")
        customer_id = (
            entity.get("customer_id")
            or entity.get("email")
            or entity.get("contact")
            or notes.get("customer_id")
        )

        return CommonTransaction(
            transaction_id=entity.get("id", f"pay_rzp_{int(datetime.now(timezone.utc).timestamp())}"),
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount=normalized_amount,
            currency=currency,
            payment_method=entity.get("method", "upi"),
            timestamp=txn_time,
            device_id=device_id,
            location=location,
            ip=ip,
            provider="razorpay",
            raw_event_type=event_name,
            metadata=notes
        )
