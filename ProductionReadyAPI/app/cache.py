import hashlib
import time
from typing import Optional, Any
from app.config import get_settings

settings = get_settings()

class ResponseCache:
    def __init__(self):
        # In production, you'd use Redis. For now, we'll use an in-memory dict.
        self._cache: dict[str, dict[str, Any]] = {}
        self.ttl = settings.cache_ttl_seconds

    def _generate_hash(self, prompt: str) -> str:
        """Create a unique MD5 hash for the prompt."""
        return hashlib.md5(prompt.strip().lower().encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        """Retrieve a response from cache if it hasn't expired."""
        cache_key = self._generate_hash(prompt)
        entry = self._cache.get(cache_key)

        if entry:
            # Check if the cache entry is still valid
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                # Cleanup expired entry
                del self._cache[cache_key]
        return None

    def set(self, prompt: str, response: str):
        """Store a response in the cache with a timestamp."""
        cache_key = self._generate_hash(prompt)
        self._cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }

    def clear(self):
        """Manually clear the cache."""
        self._cache.clear()