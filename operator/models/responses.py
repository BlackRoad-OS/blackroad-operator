"""Response models for BlackRoad Operator."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProviderStatus(str, Enum):
    """Provider availability status."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class RouteResponse(BaseModel):
    """Response from the routing endpoint."""

    success: bool = Field(..., description="Whether the request succeeded")
    provider_used: str = Field(..., description="The provider that handled the request")
    result: Any = Field(..., description="The result from the provider")
    latency_ms: float = Field(..., description="Total latency in milliseconds")
    cost_usd: Optional[float] = Field(default=None, description="Cost in USD if applicable")
    audit_id: str = Field(..., description="Audit trail ID for this request")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "provider_used": "claude",
                    "result": "The binding energy of hydrogen is -13.6 eV",
                    "latency_ms": 234.5,
                    "cost_usd": 0.0012,
                    "audit_id": "audit_abc123"
                }
            ]
        }
    }


class ProviderInfo(BaseModel):
    """Information about an available provider."""

    name: str = Field(..., description="Provider name")
    type: str = Field(..., description="Provider type (llm, compute, data, edge)")
    status: ProviderStatus = Field(..., description="Current status")
    capabilities: list[str] = Field(default_factory=list, description="What this provider can do")
    avg_latency_ms: Optional[float] = Field(default=None, description="Average latency")
    cost_per_request: Optional[float] = Field(default=None, description="Cost per request in USD")
    endpoint: Optional[str] = Field(default=None, description="Endpoint URL if applicable")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "claude",
                    "type": "llm",
                    "status": "online",
                    "capabilities": ["chat", "analysis", "coding", "reasoning"],
                    "avg_latency_ms": 500,
                    "cost_per_request": 0.003
                }
            ]
        }
    }


class HealthStatus(BaseModel):
    """Health status for the operator and all providers."""

    operator_status: str = Field(default="healthy", description="Operator status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    providers: dict[str, ProviderInfo] = Field(default_factory=dict, description="Provider statuses")
    total_requests_24h: int = Field(default=0, description="Requests in last 24 hours")
    avg_latency_24h_ms: float = Field(default=0, description="Average latency in last 24 hours")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operator_status": "healthy",
                    "timestamp": "2026-01-12T12:00:00Z",
                    "providers": {},
                    "total_requests_24h": 15234,
                    "avg_latency_24h_ms": 342.1
                }
            ]
        }
    }
