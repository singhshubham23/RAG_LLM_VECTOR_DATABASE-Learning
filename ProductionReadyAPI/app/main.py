import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langsmith import traceable
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent import ProductionAgent
from app.cache import ResponseCache
from app.config import get_settings
from app.models import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
)
from app.monitoring import MetricsCollector, RequestTimer, get_logger

# Initialize environment variables
load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
# Don't forget the exception handler for when users hit the limit!
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)