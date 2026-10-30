# Production Dockerfile for FastAPI Backend
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system utilities required for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application code
COPY backend /app/backend

# Copy frozen Phase 5D processed data required by API services
COPY data/processed /app/data/processed

# Set PYTHONPATH so 'app' package imports work cleanly
ENV PYTHONPATH=/app/backend

WORKDIR /app/backend

EXPOSE 8000

# Healthcheck endpoint check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Production execution using Uvicorn without --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
