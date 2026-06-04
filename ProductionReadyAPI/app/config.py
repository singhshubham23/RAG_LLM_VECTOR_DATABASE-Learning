"""
Centralized configuration management for the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    groq_api_key: str
    primary_model: str = "llama-3.3-70b-versatile"
    fallback_model: str = "llama-3.1-8b-instant"

    # LangSmith
    langchain_tracing_v2: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "production-api"

    # App Config
    app_env: str = "development"
    log_level: str = "INFO"
    rate_limit: str = "60/minute"
    cache_ttl_seconds: int = 300
    max_retries: int = 3

    # Pydantic Configuration
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"
    
@lru_cache()
def get_settings() -> Settings:
    """Get the application settings, cached for performance."""
    return Settings()    