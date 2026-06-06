import time
from typing import Dict, Any, Tuple
from langchain_groq import ChatGroq
from langsmith import traceable

from app.config import get_settings
from app.security import SecurityPipeline
from app.cache import ResponseCache
from app.monitoring import monitor

settings = get_settings()

class ProductionAgent:
    def __init__(self):
        # Initialize Groq client using central environment settings
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.primary_model,
            temperature=0.7
        )
        self.security = SecurityPipeline()
        self.cache = ResponseCache()

    @traceable(name="production_agent_run")
    def run(self, user_input: str) -> Tuple[Dict[str, Any], int]:
        """
        Executes the secured pipeline.
        Returns: A tuple containing (response_payload_dict, HTTP_status_code)
        """
        start_time = time.perf_counter()

        # 1. Input Validation and Sanitization Guardrail
        is_safe, clean_input, error_msg = self.security.process_input(user_input)
        if not is_safe:
            monitor.log_security_event("Prompt Injection / Malicious Input Blocked", error_msg)
            return {"error": "Security validation failed", "details": error_msg}, 400

        # 2. Performance layer: Cache Lookup
        cached_response = self.cache.get(clean_input)
        if cached_response is not None:
            processing_time = (time.perf_counter() - start_time) * 1000
            monitor.log_performance("Cached Request Resolve", processing_time)
            return {
                "response": cached_response,
                "model_used": settings.primary_model,
                "cached": True,
                "processing_time_ms": round(processing_time, 2)
            }, 200

        # 3. LLM Execution Engine
        try:
            llm_start = time.perf_counter()
            response = self.llm.invoke(clean_input)
            llm_duration = (time.perf_counter() - llm_start) * 1000
            monitor.log_performance("Groq Live API Call", llm_duration)
        except Exception as e:
            monitor.logger.error(f"Upstream Groq LLM Failure: {str(e)}")
            return {"error": "Upstream model failure", "details": str(e)}, 500

        # 4. Output Data Leak Prevention Guardrail
        is_output_safe, final_output, output_error = self.security.process_output(response.content)
        if not is_output_safe:
            monitor.log_security_event("Sensitive Output Blocked / Leak Prevention triggered", output_error)
            return {"error": "Security validation failed on generation", "details": output_error}, 500

        # 5. Commit sanitized result to Cache Layer
        self.cache.set(clean_input, final_output)

        processing_time = (time.perf_counter() - start_time) * 1000
        return {
            "response": final_output,
            "model_used": settings.primary_model,
            "cached": False,
            "processing_time_ms": round(processing_time, 2)
        }, 200

# Global Dependency injection target for FastAPI
_agent_instance = None

def get_agent() -> ProductionAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductionAgent()
    return _agent_instance