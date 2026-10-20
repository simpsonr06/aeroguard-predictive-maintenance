# ==============================================================================
# AeroGuard 2.0 / 2.1 — FastAPI Predictive Maintenance Backend
# Multi-stage lightweight Python container
# ==============================================================================

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src"

WORKDIR /app

# Install curl for reliable container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source, models, and benchmark data
COPY src/ /app/src/
COPY models/ /app/models/
COPY data/ /app/data/
COPY reports/ /app/reports/

# Create non-root system user for security compliance
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Periodic health check against FastAPI health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "aircraft_pm.api:app", "--host", "0.0.0.0", "--port", "8000"]
