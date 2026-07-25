# Production Secure AI Gateway

A production-oriented FastAPI gateway for serving chat requests through Groq-hosted language models. The API adds request validation, prompt-injection detection, PII masking, output validation, response caching, rate limiting, structured logging, health checks, and lightweight operational metrics around the model call.

## Features

- FastAPI application with automatic OpenAPI documentation.
- Groq LLM integration through LangChain (`ChatGroq`).
- Primary model configuration with a configured fallback model name.
- Prompt-injection detection for common jailbreak and instruction-override patterns.
- Input normalization and masking of email addresses, phone numbers, SSNs, and credit-card-like values.
- Output validation that blocks responses containing sensitive terms and masks detected PII.
- In-memory response cache with configurable TTL and normalized, hashed prompt keys.
- Per-client rate limiting of `60/minute` on `POST /chat` by default.
- Request, performance, security-event, and application lifecycle logging.
- Health and metrics endpoints for deployment probes and basic observability.
- Docker and Docker Compose configuration.
- Render deployment template.

## Architecture

```text
Client
  |
  v
FastAPI /chat
  |-- request validation (Pydantic)
  |-- rate limiting (SlowAPI)
  v
ProductionAgent
  |-- prompt-injection check
  |-- PII masking and input normalization
  |-- in-memory cache lookup
  |-- Groq model invocation
  |-- output validation and PII masking
  |-- cache write
  v
JSON response + monitoring metrics
```

The application creates a singleton `ProductionAgent` through FastAPI dependency injection. The agent owns the Groq client, security pipeline, and cache instance.

## Project structure

```text
.
├── app/
│   ├── main.py          # FastAPI app and HTTP endpoints
│   ├── agent.py         # Secured LLM execution pipeline
│   ├── security.py      # Injection, PII, and output guardrails
│   ├── cache.py         # TTL-based in-memory response cache
│   ├── config.py        # Environment-backed settings
│   ├── models.py        # Pydantic request and response models
│   └── monitoring.py    # Logging and system statistics
├── tests/
│   ├── test_cache.py    # Cache behavior script
│   ├── test_security.py # Security pipeline script
│   ├── test_api.py      # API test module placeholder
│   └── stress_test.py   # End-to-end scenario script (see note below)
├── Dockerfile
├── Docker-Compose.yml
├── render.yml
├── pyproject.toml
└── main.py              # Placeholder package entry point
```

## Requirements

- Python 3.11 or newer
- A Groq API key
- Docker and Docker Compose (optional)

## Configuration

Create a `.env` file in the project root. Never commit real credentials.

```env
GROQ_API_KEY=your_groq_api_key

# Model configuration
PRIMARY_MODEL=llama-3.3-70b-versatile
FALLBACK_MODEL=llama-3.1-8b-instant

# LangSmith tracing (optional)
LANGCHAIN_TRACING_V2=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=production-api

# Application settings
APP_ENV=development
LOG_LEVEL=INFO
RATE_LIMIT=60/minute
CACHE_TTL_SECONDS=300
MAX_RETRIES=3
```

`GROQ_API_KEY` is required. Settings are loaded by `pydantic-settings` from environment variables and `.env`. The current agent initializes the configured primary model; `FALLBACK_MODEL` and `MAX_RETRIES` are available settings but are not yet used by the model execution code.

## Local development

Install the project and development dependencies with your preferred Python environment manager. Using pip:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -e .
pip install pytest httpx
```

Start the API from the repository root:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service is then available at `http://localhost:8000`.

The root landing page links to:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

The top-level `main.py` currently prints a greeting and is not the API entry point. Use `app.main:app` when running Uvicorn.

## API reference

### `GET /`

Returns a small HTML landing page with links to documentation and operational endpoints.

### `POST /chat`

Accepts a chat message, applies the security pipeline, retrieves a cached result when available, or calls the configured Groq model.

Request:

```json
{
  "message": "Explain how a REST API works.",
  "thread_id": "demo-thread"
}
```

`message` must contain 1–10,000 characters. `thread_id` defaults to `default` and is returned as metadata; conversation history is not currently stored or sent to the model.

Example with curl:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain how a REST API works.","thread_id":"demo-thread"}'
```

Successful response:

```json
{
  "response": "...",
  "thread_id": "demo-thread",
  "model_used": "llama-3.3-70b-versatile",
  "cached": false,
  "processing_time_ms": 842.31,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

Possible errors include:

- `400` — security validation failed, such as a detected prompt injection.
- `429` — the client exceeded the rate limit.
- `500` — the upstream Groq model failed or generated blocked output.

Error responses contain `error`, `details`, and a generated `request_id` where applicable.

### `GET /health`

Returns liveness information, configured environment, API version, cache status, and security guardrail status.

### `GET /metrics`

Returns in-process counters for total requests, errors, average latency, cache hit rate, and error rate. Token counters currently return zero because token usage is not extracted from Groq responses.

## Security pipeline

For each chat request:

1. Pydantic validates the request shape and message length.
2. SlowAPI applies the endpoint rate limit.
3. Common prompt-injection phrases are rejected.
4. Input PII is masked and whitespace/template markers are normalized.
5. The normalized prompt is checked against the in-memory cache.
6. A cache miss is sent to the Groq model.
7. Generated output is checked for sensitive terms and PII is masked.
8. Safe output is cached and returned.

These controls are baseline application guardrails, not a complete security boundary. For production use, add authentication/authorization, durable and shared rate limiting, secret management, audit storage, stronger content policy enforcement, and security testing.

## Cache behavior

The current cache is process-local and in-memory. Cache keys are MD5 hashes of the lowercased, trimmed prompt, and entries expire after `CACHE_TTL_SECONDS` (300 seconds by default). A restart, multiple worker processes, or multiple containers will not share cache data. Redis or another shared cache is recommended for horizontally scaled production deployments.

## Docker

Build and run the service with Docker Compose:

```bash
docker compose -f Docker-Compose.yml up --build
```

The API is exposed on port `8000`. Compose mounts `./app` into the container for local development and loads environment variables from `.env`.

Build and run the image directly:

```bash
docker build -t production-secure-gateway .
docker run --rm -p 8000:8000 --env-file .env production-secure-gateway
```

## Render deployment

`render.yml` defines a Docker web service named `secure-ai-gateway`. Before deploying, replace the placeholder repository URL and configure `GROQ_API_KEY` as a secret environment variable in Render. Review the selected region, plan, and production settings before going live.

## Tests and validation scripts

The files under `tests/` currently use callable scripts and do not define normal `pytest` test functions. Run the available checks directly:

```bash
python -X utf8 -m tests.test_security
python -X utf8 -m tests.test_cache
```

`tests/stress_test.py` is intended as an end-to-end scenario runner, but it currently imports `GroqAgent` while the implementation exposes `ProductionAgent`. Update that import before running it, and ensure `GROQ_API_KEY` is configured because it makes live model calls.

The `-X utf8` option is useful on Windows terminals that cannot print the check-mark characters used by these scripts. Running the files directly can also fail to resolve the `app` package, so run them as modules from the repository root.

For a quick API smoke test, start the server and call `/health` and `/chat` with the examples above.

## Operational notes

- Metrics are stored in process memory and reset on restart.
- The rate-limit decorator currently uses the literal `60/minute`; changing `RATE_LIMIT` alone does not change that decorator.
- The configured fallback model is not automatically invoked if the primary model fails.
- `LANGCHAIN_TRACING_V2` and LangSmith credentials enable tracing configuration, but tracing requires valid LangSmith setup.
- Do not expose `/metrics` publicly without considering whether the operational data should be protected.

## License

No license file is currently included in this repository. Add a license before distributing the project.
