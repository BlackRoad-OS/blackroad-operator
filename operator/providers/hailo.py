"""Hailo-8 edge inference provider implementation."""

from typing import Any, Optional
import httpx

from .base import BaseProvider
from ..config import get_settings


class HailoProvider(BaseProvider):
    """Provider for Hailo-8 local edge inference (26 TOPS)."""

    name = "hailo"
    provider_type = "edge"
    capabilities = ["inference", "vision", "fast", "local", "edge"]

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self._endpoint = settings.hailo_endpoint
        self._client = httpx.AsyncClient(timeout=10.0)

    async def execute(
        self,
        query: str,
        model: str = "default",
        input_data: Any = None,
        **kwargs
    ) -> Any:
        """Execute inference on Hailo-8."""
        try:
            response = await self._client.post(
                f"{self._endpoint}/inference",
                json={
                    "model": model,
                    "input": input_data or query,
                    "options": kwargs,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "endpoint": self._endpoint}

    async def health_check(self) -> bool:
        """Check if Hailo endpoint is accessible."""
        try:
            response = await self._client.get(f"{self._endpoint}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available models on Hailo."""
        try:
            response = await self._client.get(f"{self._endpoint}/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception:
            return []

    async def get_stats(self) -> dict:
        """Get Hailo performance statistics."""
        try:
            response = await self._client.get(f"{self._endpoint}/stats")
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"error": "Could not retrieve stats", "tops": 26}
