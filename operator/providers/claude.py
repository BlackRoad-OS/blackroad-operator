"""Claude (Anthropic) provider implementation."""

from typing import Any, Optional
import anthropic

from .base import BaseProvider
from ..config import get_settings


class ClaudeProvider(BaseProvider):
    """Provider for Anthropic's Claude API."""

    name = "claude"
    provider_type = "llm"
    capabilities = ["chat", "analysis", "coding", "reasoning", "math", "writing"]

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self._client = None
        if settings.anthropic_api_key:
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.default_model

    async def execute(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Any:
        """Execute a request against Claude."""
        if not self._client:
            raise ValueError("Anthropic API key not configured")

        messages = [{"role": "user", "content": query}]

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=messages,
        )

        return {
            "content": response.content[0].text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }

    async def health_check(self) -> bool:
        """Check if Claude API is accessible."""
        if not self._client:
            return False
        try:
            # Simple health check with minimal tokens
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return response.content is not None
        except Exception:
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD based on token usage."""
        # Claude Sonnet pricing (approximate)
        input_cost = (input_tokens / 1_000_000) * 3.0  # $3 per 1M input tokens
        output_cost = (output_tokens / 1_000_000) * 15.0  # $15 per 1M output tokens
        return input_cost + output_cost
