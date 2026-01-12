"""Audit logging models for BlackRoad Operator."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class AuditEntry(BaseModel):
    """Audit log entry for every operation."""

    id: str = Field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Request info
    request_type: str = Field(..., description="Type of request (route, chat, physics, data)")
    request_query: str = Field(..., description="The original query/request")
    request_context: Optional[dict[str, Any]] = Field(default=None)

    # Routing info
    intent_detected: str = Field(..., description="Detected intent type")
    provider_selected: str = Field(..., description="Provider that was selected")
    provider_alternatives: list[str] = Field(default_factory=list, description="Other providers considered")

    # Response info
    success: bool = Field(..., description="Whether the request succeeded")
    response_summary: Optional[str] = Field(default=None, description="Summary of response")
    error_message: Optional[str] = Field(default=None, description="Error if failed")

    # Metrics
    latency_ms: float = Field(..., description="Total latency")
    provider_latency_ms: float = Field(..., description="Provider-only latency")
    cost_usd: Optional[float] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)

    # Metadata
    client_ip: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    api_version: str = Field(default="v1")

    def to_json_line(self) -> str:
        """Convert to JSON line for logging."""
        return self.model_dump_json() + "\n"
