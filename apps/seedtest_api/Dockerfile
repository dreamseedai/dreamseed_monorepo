# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for FastAPI (Python 3.11) targeting Cloud Run

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies separately for better caching
COPY apps/seedtest_api/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Final image
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN useradd -m appuser
WORKDIR /app

# Copy installed site-packages from builder layer
COPY --from=base /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application code into two locations to support both import styles:
# - seedtest_api.* (for uvicorn and direct module runs)
# - apps.seedtest_api.* (for jobs that reference apps.*)
COPY apps/seedtest_api/ /app/seedtest_api/
COPY apps/ /app/apps/

# Expose Cloud Run port
EXPOSE 8080

# Healthcheck (optional; Cloud Run uses container exit code; keep simple)
# HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:${PORT}/health || exit 1

USER appuser

# Start FastAPI with Uvicorn using the package module path
CMD ["uvicorn", "seedtest_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
