"""Request models for BlackRoad Operator."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    """Types of intents the operator can route."""
    PHYSICS = "physics"
    LANGUAGE = "language"
    DATA = "data"
    INFERENCE = "inference"
    UNKNOWN = "unknown"


class RouteRequest(BaseModel):
    """Main routing request - operator determines best provider."""

    query: str = Field(..., description="The user's query or request")
    context: Optional[dict[str, Any]] = Field(default=None, description="Additional context")
    preferred_provider: Optional[str] = Field(default=None, description="Preferred provider if any")
    max_cost: Optional[float] = Field(default=None, description="Maximum cost in USD")
    require_local: bool = Field(default=False, description="Require local/edge processing")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What is the binding energy of hydrogen?",
                    "context": {"domain": "physics"},
                    "require_local": False
                }
            ]
        }
    }


class ChatRequest(BaseModel):
    """Direct chat request with automatic provider selection."""

    message: str = Field(..., description="The message to send")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    system_prompt: Optional[str] = Field(default=None, description="System prompt override")
    model: Optional[str] = Field(default=None, description="Specific model to use")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Explain quantum entanglement in simple terms",
                    "conversation_id": "conv_123"
                }
            ]
        }
    }


class PhysicsRequest(BaseModel):
    """Physics calculation request routed to NumPy/SciPy."""

    operation: str = Field(..., description="The physics operation to perform")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    precision: int = Field(default=15, description="Decimal precision")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operation": "hydrogen_binding_energy",
                    "parameters": {"n": 1},
                    "precision": 10
                }
            ]
        }
    }


class DataRequest(BaseModel):
    """Data operation request routed to Salesforce/DB."""

    operation: str = Field(..., description="The data operation (query, create, update, delete)")
    object_type: str = Field(..., description="The object type (Contact, Account, etc.)")
    data: Optional[dict[str, Any]] = Field(default=None, description="Data for create/update")
    query: Optional[str] = Field(default=None, description="SOQL query for query operation")
    record_id: Optional[str] = Field(default=None, description="Record ID for update/delete")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operation": "query",
                    "object_type": "Contact",
                    "query": "SELECT Id, Name FROM Contact LIMIT 10"
                }
            ]
        }
    }
