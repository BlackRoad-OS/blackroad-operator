"""OpenAI GPT provider implementation."""

from typing import Any, Optional
import openai

from .base import BaseProvider
from ..config import get_settings


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's GPT API (fallback)."""

    name = "gpt"
    provider_type = "llm"
    capabilities = ["chat", "analysis", "coding", "reasoning"]

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self._client = None
        if settings.openai_api_key:
            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.fallback_model

    async def execute(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Any:
        """Execute a request against GPT."""
        if not self._client:
            raise ValueError("OpenAI API key not configured")

        messages = [
            {"role": "system", "content": system_prompt or "You are a helpful assistant."},
            {"role": "user", "content": query},
        ]

        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=messages,
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            "finish_reason": choice.finish_reason,
        }

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self._client:
            return False
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return response.choices is not None
        except Exception:
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD based on token usage."""
        # GPT-4 pricing (approximate)
        input_cost = (input_tokens / 1_000_000) * 30.0
        output_cost = (output_tokens / 1_000_000) * 60.0
        return input_cost + output_cost
