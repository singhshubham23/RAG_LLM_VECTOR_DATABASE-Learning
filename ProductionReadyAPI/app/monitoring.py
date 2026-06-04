import time
import logging
import sys
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()

class AppMonitor:
    def __init__(self):
        # 1. Setup Structured Logging
        self.logger = logging.getLogger("production_api")
        self.logger.setLevel(settings.log_level)
        
        # Format for logs: Timestamp - Level - Message
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def log_request(self, path: str, method: str):
        """Log incoming API requests."""
        self.logger.info(f"Incoming Request: {method} {path}")

    def log_performance(self, operation: str, duration_ms: float):
        """Log how long operations (like LLM calls) take."""
        self.logger.info(f"Performance: {operation} took {duration_ms:.2f}ms")

    def log_security_event(self, event_type: str, details: str):
        """Log blocked injections or PII detections."""
        self.logger.warning(f"SECURITY ALERT: {event_type} - {details}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Basic health metrics for the health check endpoint."""
        return {
            "log_level": settings.log_level,
            "tracing_enabled": settings.langchain_tracing_v2,
            "environment": settings.app_env,
            "uptime_reference": time.monotonic()
        }

# Global monitor instance
monitor = AppMonitor()