"""Base provider interface and registry."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
import time

from ..models.responses import ProviderInfo, ProviderStatus


class BaseProvider(ABC):
    """Base class for all providers."""

    name: str = "base"
    provider_type: str = "unknown"
    capabilities: list[str] = []

    def __init__(self):
        self._status = ProviderStatus.UNKNOWN
        self._last_check = None
        self._latency_samples: list[float] = []

    @abstractmethod
    async def execute(self, query: str, **kwargs) -> Any:
        """Execute a request against this provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass

    def get_info(self) -> ProviderInfo:
        """Get provider information."""
        avg_latency = None
        if self._latency_samples:
            avg_latency = sum(self._latency_samples) / len(self._latency_samples)

        return ProviderInfo(
            name=self.name,
            type=self.provider_type,
            status=self._status,
            capabilities=self.capabilities,
            avg_latency_ms=avg_latency,
        )

    async def execute_with_metrics(self, query: str, **kwargs) -> tuple[Any, float]:
        """Execute and track latency."""
        start = time.perf_counter()
        result = await self.execute(query, **kwargs)
        latency_ms = (time.perf_counter() - start) * 1000

        # Track latency (keep last 100 samples)
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > 100:
            self._latency_samples.pop(0)

        return result, latency_ms


class ProviderRegistry:
    """Registry of all available providers."""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def list_all(self) -> list[ProviderInfo]:
        """List all registered providers."""
        return [p.get_info() for p in self._providers.values()]

    def get_by_capability(self, capability: str) -> list[BaseProvider]:
        """Get all providers with a specific capability."""
        return [p for p in self._providers.values() if capability in p.capabilities]

    async def health_check_all(self) -> dict[str, ProviderInfo]:
        """Health check all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                healthy = await provider.health_check()
                provider._status = ProviderStatus.ONLINE if healthy else ProviderStatus.OFFLINE
            except Exception:
                provider._status = ProviderStatus.OFFLINE
            results[name] = provider.get_info()
        return results


# Global registry instance
registry = ProviderRegistry()
