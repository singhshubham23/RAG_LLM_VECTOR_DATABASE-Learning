import time
from app.cache import ResponseCache
from app.config import get_settings

def run_cache_test():
    cache = ResponseCache()
    settings = get_settings()
    
    prompt = "How does photosynthesis work?"
    mock_response = "Plants use sunlight to make food."

    print(f"\n--- Starting Cache Test (TTL: {settings.cache_ttl_seconds}s) ---")

    # TEST 1: Initial Miss
    print("\nTest 1: Initial Lookup")
    start_time = time.time()
    result = cache.get(prompt)
    print(f"Result: {result} | (Expected: None)")
    
    # TEST 2: Set and Hit
    print("\nTest 2: Store and Retrieve")
    cache.set(prompt, mock_response)
    hit = cache.get(prompt)
    print(f"Result: {hit} | (Expected: {mock_response})")
    if hit == mock_response:
        print("✅ Cache HIT successful!")

    # TEST 3: Normalization Check
    print("\nTest 3: Normalization (Checking case sensitivity/spacing)")
    normalized_hit = cache.get("  HOW DOES PHOTOSYNTHESIS WORK?  ")
    if normalized_hit == mock_response:
        print("✅ Cache normalization successful!")

    # TEST 4: Expiration (The "Time Travel" Test)
    print("\nTest 4: Expiration Check")
    print("Simulating time passing (manually overriding timestamp)...")
    
    # We cheat a bit for the test: reach in and set the timestamp to the past
    cache_key = cache._generate_hash(prompt)
    cache._cache[cache_key]["timestamp"] = time.time() - (settings.cache_ttl_seconds + 1)
    
    expired_result = cache.get(prompt)
    if expired_result is None:
        print("✅ Cache expiration successful! Entry was cleared.")
    else:
        print("❌ Cache expiration FAILED. Stale data was returned.")

if __name__ == "__main__":
    run_cache_test()