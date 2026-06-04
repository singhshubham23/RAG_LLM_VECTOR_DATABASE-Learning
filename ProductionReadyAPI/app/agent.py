import time
from langchain_groq import ChatGroq
from app.config import get_settings
from app.security import SecurityPipeline
from app.cache import ResponseCache
from app.monitoring import monitor
from langsmith import traceable

settings = get_settings()

class GroqAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.primary_model,
            temperature=0.7
        )
        self.security = SecurityPipeline()
        self.cache = ResponseCache()

    @traceable(name="agent_run")
    def run(self, user_input: str):
        # 1. Security Check
        is_safe, clean_input, err = self.security.process_input(user_input)
        if not is_safe:
            return {"error": err, "status": 400}

        # 2. Cache Check
        cached_res = self.cache.get(clean_input)
        if cached_res:
            return {"response": cached_res, "status": 200, "cached": True}

        # 3. LLM Call (Performance Tracking)
        start_time = time.perf_counter()
        
        # --- THIS LINE WAS LIKELY CAUSING YOUR ERROR ---
        response = self.llm.invoke(clean_input) 
        
        duration = (time.perf_counter() - start_time) * 1000
        monitor.log_performance("Groq LLM Call", duration)

        # 4. Output Guardrail
        is_valid, final_output, err = self.security.process_output(response.content)
        if not is_valid:
            return {"error": err, "status": 500}

        # 5. Save to Cache
        self.cache.set(clean_input, final_output)

        return {"response": final_output, "status": 200, "cached": False}

def get_agent():
    return GroqAgent()