"""
Payment Provider Abstraction Layer and Canonical Transaction Schema.

BharatSHIELD Core Principle:
A payment provider only ever supplies a transaction or event.
BharatSHIELD core intelligence (risk engine, features, SHAP, policy, dashboard)
remains strictly provider-independent.
"""

import abc
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator


class CommonTransaction(BaseModel):
    """
    Canonical Transaction Schema.
    Every payment provider adapter normalizes its proprietary webhook or event payload
    into this standard contract before BharatSHIELD feature engineering and risk scoring.
    """
    transaction_id: str = Field(..., description="Universal or provider-issued transaction ID")
    merchant_id: str = Field(default="MER_razorpay_001", description="BharatSHIELD merchant ID")
    customer_id: Optional[str] = Field(default=None, description="Customer or user identifier from provider")
    amount: float = Field(..., gt=0, description="Transaction amount in primary currency unit (e-g- INR Rupees, not paise)")
    currency: str = Field(default="INR", description="ISO 4217 Currency Code")
    payment_method: str = Field(default="upi", description="Normalized method: upi, card, netbanking, wallet")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Transaction execution timestamp")
    
    # Telemetry and contextual signals
    device_id: Optional[str] = Field(default=None, description="Device footprint or identifier")
    location: Optional[str] = Field(default=None, description="City, state, or location descriptor")
    ip: Optional[str] = Field(default=None, description="Client IP address")
    
    # Provider attribution
    provider: str = Field(..., description="Originating PSP name: razorpay, stub, hdfc, phonepe, etc.")
    raw_event_type: Optional[str] = Field(default=None, description="Original provider event name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional non-standard provider metadata")

    @field_validator("payment_method")
    @classmethod
    def standardize_method(cls, v: str) -> str:
        clean = str(v).strip().lower()
        if "upi" in clean:
            return "UPI"
        if "credit" in clean:
            return "Credit Card"
        if "debit" in clean:
            return "Debit Card"
        if "card" in clean:
            return "Credit Card"
        if any(m in clean for m in ["netbanking", "net_banking", "bank"]):
            return "Net Banking"
        if "wallet" in clean:
            return "Wallet"
        return v

    def to_feature_dict(self) -> Dict[str, Any]:
        """
        Converts normalized transaction and metadata into a feature dictionary
        compatible with the RiskEngine inference pipeline.
        """
        features = {
            "transaction_id": self.transaction_id,
            "merchant_id": self.merchant_id,
            "transaction_amount": self.amount,
            "payment_method": self.payment_method,
            "transaction_hour": self.timestamp.hour,
            "transaction_day": self.timestamp.weekday(),
            "device_id": self.device_id,
            "ip_address": self.ip,
            "location": self.location,
        }
        if isinstance(self.metadata, dict):
            features.update(self.metadata)
            if "signals" in self.metadata and isinstance(self.metadata["signals"], dict):
                features.update(self.metadata["signals"])
        return features


class PaymentProvider(abc.ABC):
    """
    Abstract Base Class for all Payment Provider Adapters.
    New payment gateways implement this interface.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier matching transactions.provider."""
        pass

    @abc.abstractmethod
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: Union[str, List[str], tuple]
    ) -> bool:
        """
        Verifies provider webhook cryptographic signature.
        Supports versioned secrets (list of [current_secret, previous_secret])
        to facilitate zero-downtime secret rotation.
        """
        pass

    @abc.abstractmethod
    def parse_webhook(
        self,
        payload: Union[Dict[str, Any], bytes],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Parses raw HTTP webhook body and extracts relevant event entity.
        """
        pass

    @abc.abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> CommonTransaction:
        """
        Converts provider-specific event dictionary into BharatSHIELD CommonTransaction.
        """
        pass
