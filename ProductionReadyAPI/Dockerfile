FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml ./

# Install runtime dependencies directly from pyproject.toml.
RUN pip install --no-cache-dir \
    fastapi>=0.136.3 \
    langchain-groq>=1.1.2 \
    langgraph>=1.2.2 \
    langsmith>=0.8.7 \
    pydantic-settings>=2.14.1 \
    python-dotenv>=1.2.2 \
    slowapi>=0.1.9 \
    uvicorn>=0.49.0

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
