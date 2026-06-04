"""
API REQUEST AND RESPONSE MODELS
Pydantic models for validating and structuring API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone


class chatRequest(BaseModel):
    """
    Model for incoming chat requests.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's message to the chatbot.",
    )

    thread_id: str = Field(
        ...,
        default="default",
        description="Conversation thread ID.",
    )


class chatResponse(BaseModel):
    """Chat response return to Client"""

    response: str
    thread_id: str
    model_used: str
    cached: bool
    processing_time_ms: float
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The time the response was generated.",
    )


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    environment: str
    version: str = "1.0.0"
    checks: dict = {}


class MetricsResponse(BaseModel):
    """Metrics response model"""

    total_requests: int
    total_errors: int
    error_rate: str
    avg_latency_ms: float
    cache_hit_rate: str
    total_input_tokens: int
    total_output_tokens: int


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    details: str = None
    request_id: str = None
