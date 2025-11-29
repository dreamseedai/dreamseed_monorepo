# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DreamSeed Backend - Dockerfile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FROM python:3.11-slim

LABEL maintainer="DreamSeed AI <dev@dreamseed.ai>"
LABEL description="DreamSeed Backend - FastAPI + CAT Engine"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (generated from backend/.venv)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (all backend files)
COPY . .

# Create non-root user
RUN useradd -m -u 1000 dreamseed && \
    chown -R dreamseed:dreamseed /app

USER dreamseed

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Startup script (already copied with COPY . .)
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER dreamseed

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--loop", "asyncio"]
