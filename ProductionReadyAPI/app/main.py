import os
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.agent import ProductionAgent, get_agent
from app.config import get_settings
from app.models import (
    chatRequest,  # Lowercase class names to match your Pydantic layer snippet
    chatResponse,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
)
from app.monitoring import monitor

settings = get_settings()

# Internal metrics aggregator for the telemetry dashboard endpoint
GLOBAL_METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "total_latency_ms": 0.0,
    "cache_hits": 0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown clean routines for the SaaS API Gateway."""
    monitor.logger.info(
        f"Booting Secure AI Gateway under environment: {settings.app_env}"
    )
    # Force instantiation of dependencies on boot
    get_agent()
    yield
    monitor.logger.info("Tearing down Secure AI Gateway services...")


# Initialize App Instance
app = FastAPI(title="Production Secure AI Gateway", version="1.0.0", lifespan=lifespan)

# Setup Layer 7 Protection Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Intercepts rate limits and bubbles up an explicit ErrorResponse payload."""
    GLOBAL_METRICS["total_errors"] += 1
    error_payload = ErrorResponse(
        error="Rate limit exceeded",
        details=f"Maximum allowed requests breached. Limit: {exc.detail}",
        request_id=str(uuid4()),
    )
    return JSONResponse(status_code=429, content=error_payload.model_dump())


# --- CORE ENDPOINTS ---


@app.post(
    "/chat",
    response_model=chatResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
@limiter.limit("60/minute")  # Configurable tier throttling
async def chat(
    request: Request, payload: chatRequest, agent: ProductionAgent = Depends(get_agent)
):
    """
    Main SaaS Secured Chat Endpoint.
    Applies real-time rate-limiting, injection tracking, PII sanitization, and caching.
    """
    req_id = str(uuid4())
    GLOBAL_METRICS["total_requests"] += 1
    monitor.log_request(path="/chat", method="POST")

    start_time = time.perf_counter()

    # Process request using our core agent pipeline
    result, status_code = agent.run(payload.message)

    execution_time_ms = (time.perf_counter() - start_time) * 1000
    GLOBAL_METRICS["total_latency_ms"] += execution_time_ms

    if status_code != 200:
        GLOBAL_METRICS["total_errors"] += 1
        error_payload = ErrorResponse(
            error=result.get("error", "Internal Processing Failure"),
            details=result.get("details", ""),
            request_id=req_id,
        )
        return JSONResponse(status_code=status_code, content=error_payload.model_dump())

    # Record metrics details
    if result["cached"]:
        GLOBAL_METRICS["cache_hits"] += 1

    # Format out to our Pydantic interface model specification
    return chatResponse(
        response=result["response"],
        thread_id=payload.thread_id,
        model_used=result["model_used"],
        cached=result["cached"],
        processing_time_ms=result["processing_time_ms"],
    )


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe monitoring endpoint."""
    stats = monitor.get_system_stats()
    return HealthResponse(
        status="healthy",
        environment=stats["environment"],
        version="1.0.0",
        checks={"cache_layer": "online", "security_guardrails": "active"},
    )


@app.get("/metrics", response_model=MetricsResponse)
def system_metrics():
    """SaaS Telemetry Dashboard metrics readout endpoint."""
    req_count = GLOBAL_METRICS["total_requests"]
    err_count = GLOBAL_METRICS["total_errors"]
    hit_count = GLOBAL_METRICS["cache_hits"]
    total_lat = GLOBAL_METRICS["total_latency_ms"]

    error_rate_pct = (err_count / req_count * 100) if req_count > 0 else 0.0
    avg_latency = (total_lat / req_count) if req_count > 0 else 0.0
    hit_rate_pct = (hit_count / req_count * 100) if req_count > 0 else 0.0

    return MetricsResponse(
        total_requests=req_count,
        total_errors=err_count,
        error_rate=f"{error_rate_pct:.1f}%",
        avg_latency_ms=round(avg_latency, 2),
        cache_hit_rate=f"{hit_rate_pct:.1f}%",
        total_input_tokens=0,  # Expandable if extracting exact usage from Groq payload
        total_output_tokens=0,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
