"""
BlackRoad Operator - Main FastAPI Application

The Central Routing Layer that routes requests to the right tool at the right time.
BlackRoad is a routing company, not an AI company.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .router import router as query_router, RouteStrategy
from .audit import audit_logger, AuditEntry
from .models.requests import RouteRequest, ChatRequest, PhysicsRequest, DataRequest
from .models.responses import RouteResponse, HealthStatus, ProviderInfo

from .providers.base import registry
from .providers.claude import ClaudeProvider
from .providers.openai import OpenAIProvider
from .providers.physics import PhysicsProvider
from .providers.salesforce import SalesforceProvider
from .providers.hailo import HailoProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - setup and teardown."""
    # Startup: Register providers
    registry.register(ClaudeProvider())
    registry.register(OpenAIProvider())
    registry.register(PhysicsProvider())
    registry.register(SalesforceProvider())
    registry.register(HailoProvider())

    yield

    # Shutdown: Close audit logger
    await audit_logger.close()


app = FastAPI(
    title="BlackRoad Operator",
    description="The Central Routing Layer - Routes requests to the right tool at the right time",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Main Routing Endpoint ===

@app.post("/route", response_model=RouteResponse)
async def route_request(request: RouteRequest, req: Request) -> RouteResponse:
    """
    Main routing endpoint.

    Analyzes the query, detects intent, and routes to the best provider.
    """
    start_time = time.perf_counter()
    audit_id = f"audit_{uuid.uuid4().hex[:12]}"

    try:
        # Route the query
        strategy = RouteStrategy.AUTO
        if request.require_local:
            strategy = RouteStrategy.FASTEST

        provider, intent, alternatives = query_router.route(
            query=request.query,
            strategy=strategy,
            preferred_provider=request.preferred_provider,
            require_local=request.require_local,
        )

        # Execute against the provider
        provider_start = time.perf_counter()
        result, provider_latency = await provider.execute_with_metrics(
            request.query,
            **(request.context or {})
        )
        total_latency = (time.perf_counter() - start_time) * 1000

        # Calculate cost if applicable
        cost = None
        if hasattr(provider, 'estimate_cost') and isinstance(result, dict):
            usage = result.get('usage', {})
            if usage:
                cost = provider.estimate_cost(
                    usage.get('input_tokens', 0),
                    usage.get('output_tokens', 0)
                )

        # Log audit entry
        await audit_logger.log(AuditEntry(
            id=audit_id,
            request_type="route",
            request_query=request.query,
            request_context=request.context,
            intent_detected=intent.value,
            provider_selected=provider.name,
            provider_alternatives=alternatives,
            success=True,
            response_summary=str(result)[:200] if result else None,
            latency_ms=total_latency,
            provider_latency_ms=provider_latency,
            cost_usd=cost,
            client_ip=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ))

        return RouteResponse(
            success=True,
            provider_used=provider.name,
            result=result,
            latency_ms=total_latency,
            cost_usd=cost,
            audit_id=audit_id,
        )

    except Exception as e:
        total_latency = (time.perf_counter() - start_time) * 1000

        # Log failed request
        await audit_logger.log(AuditEntry(
            id=audit_id,
            request_type="route",
            request_query=request.query,
            request_context=request.context,
            intent_detected="unknown",
            provider_selected="none",
            provider_alternatives=[],
            success=False,
            error_message=str(e),
            latency_ms=total_latency,
            provider_latency_ms=0,
            client_ip=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ))

        raise HTTPException(status_code=500, detail=str(e))


# === Chat Endpoint ===

@app.post("/chat")
async def chat(request: ChatRequest, req: Request) -> dict:
    """
    Direct chat interface with automatic provider selection.
    """
    route_req = RouteRequest(
        query=request.message,
        context={"system_prompt": request.system_prompt} if request.system_prompt else None,
        preferred_provider=None,
    )

    response = await route_request(route_req, req)
    return {
        "message": response.result.get("content", response.result) if isinstance(response.result, dict) else response.result,
        "provider": response.provider_used,
        "audit_id": response.audit_id,
    }


# === Physics Endpoints ===

@app.post("/physics/{operation}")
async def physics_operation(operation: str, request: PhysicsRequest, req: Request) -> dict:
    """
    Physics calculation endpoint.

    Routed directly to NumPy/SciPy provider.
    """
    provider = registry.get("physics")
    if not provider:
        raise HTTPException(status_code=503, detail="Physics provider not available")

    result = await provider.execute(
        query=operation,
        operation=operation,
        **request.parameters,
    )

    return {
        "operation": operation,
        "result": result,
        "provider": "physics",
    }


@app.get("/physics/constants")
async def list_constants() -> dict:
    """List all available physical constants."""
    provider = registry.get("physics")
    if not provider:
        raise HTTPException(status_code=503, detail="Physics provider not available")

    return {
        "constants": list(provider.CONSTANTS.keys()),
        "provider": "physics",
    }


@app.get("/physics/operations")
async def list_physics_operations() -> dict:
    """List all available physics operations."""
    provider = registry.get("physics")
    if not provider:
        raise HTTPException(status_code=503, detail="Physics provider not available")

    return {
        "operations": list(provider._operations.keys()),
        "provider": "physics",
    }


# === Data Endpoints ===

@app.post("/data/{operation}")
async def data_operation(operation: str, request: DataRequest, req: Request) -> dict:
    """
    Data operation endpoint (Salesforce).
    """
    provider = registry.get("salesforce")
    if not provider:
        raise HTTPException(status_code=503, detail="Salesforce provider not available")

    result = await provider.execute(
        query=request.query or "",
        operation=operation,
        object_type=request.object_type,
        data=request.data,
        record_id=request.record_id,
    )

    return {
        "operation": operation,
        "result": result,
        "provider": "salesforce",
    }


# === Provider Management ===

@app.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List all registered providers and their status."""
    return registry.list_all()


@app.get("/providers/{name}", response_model=ProviderInfo)
async def get_provider(name: str) -> ProviderInfo:
    """Get information about a specific provider."""
    provider = registry.get(name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found: {name}")
    return provider.get_info()


# === Health & Status ===

@app.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Health check for all providers."""
    providers = await registry.health_check_all()
    stats = await audit_logger.get_stats(hours=24)

    return HealthStatus(
        operator_status="healthy",
        providers=providers,
        total_requests_24h=stats["total_requests"],
        avg_latency_24h_ms=stats["avg_latency_ms"],
    )


@app.get("/stats")
async def get_stats(hours: int = 24) -> dict:
    """Get operator statistics."""
    return await audit_logger.get_stats(hours=hours)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "BlackRoad Operator",
        "version": "1.0.0",
        "description": "The Central Routing Layer - Routes requests to the right tool at the right time",
        "thesis": "BlackRoad is a routing company, not an AI company",
        "endpoints": {
            "route": "POST /route - Main routing endpoint",
            "chat": "POST /chat - Direct chat interface",
            "physics": "POST /physics/{operation} - Physics calculations",
            "data": "POST /data/{operation} - Data operations",
            "providers": "GET /providers - List providers",
            "health": "GET /health - Health check",
            "stats": "GET /stats - Statistics",
        },
        "docs": "/docs",
    }


# Entry point for direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
