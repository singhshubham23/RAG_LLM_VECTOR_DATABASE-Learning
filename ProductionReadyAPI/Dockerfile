# Use a lightweight, official Python base image
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="."

# Establish the working directory inside the container
WORKDIR /app

# Install uv directly from the official binaries for ultra-fast builds
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/ /usr/local/bin/

# Copy only dependency definitions first to maximize Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project wrapper itself
RUN uv pip install --system -r pyproject.toml

# Copy the rest of your application source code
COPY app/ ./app/

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the production server using uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]