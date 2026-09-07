"""Payment Provider Abstraction Layer for BharatSHIELD."""

from backend.app.providers.base import CommonTransaction, PaymentProvider
from backend.app.providers.razorpay_adapter import RazorpayAdapter
from backend.app.providers.stub_adapter import StubProviderAdapter
from backend.app.providers.registry import ProviderRegistry, get_provider

__all__ = [
    "CommonTransaction",
    "PaymentProvider",
    "RazorpayAdapter",
    "StubProviderAdapter",
    "ProviderRegistry",
    "get_provider",
]
