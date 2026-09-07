"""
Payment Provider Registry and Factory.
"""

from typing import Dict, Optional, List
from backend.app.providers.base import PaymentProvider
from backend.app.providers.razorpay_adapter import RazorpayAdapter
from backend.app.providers.stub_adapter import StubProviderAdapter


class ProviderRegistry:
    """
    Central Registry for Payment Provider Adapters.
    Allows dynamic adapter lookup without touching the risk engine.
    """

    _adapters: Dict[str, PaymentProvider] = {}

    @classmethod
    def register(cls, adapter: PaymentProvider) -> None:
        cls._adapters[adapter.provider_name.lower()] = adapter

    @classmethod
    def get(cls, provider_name: str) -> Optional[PaymentProvider]:
        return cls._adapters.get(provider_name.lower())

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._adapters.keys())


# Register built-in adapters
ProviderRegistry.register(RazorpayAdapter())
ProviderRegistry.register(StubProviderAdapter())


def get_provider(provider_name: str) -> Optional[PaymentProvider]:
    return ProviderRegistry.get(provider_name)
