# Multi-stage Docker build for dcmaidbot
FROM python:3.13-slim AS builder

# Build arguments for deployment information
ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

# Set as environment variables
ENV GIT_COMMIT=${GIT_COMMIT}
ENV IMAGE_TAG=${IMAGE_TAG}
ENV BUILD_TIME=${BUILD_TIME}
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-slim

# Build args
ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

# Environment variables
ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV GIT_COMMIT=${GIT_COMMIT}
ENV IMAGE_TAG=${IMAGE_TAG}
ENV BUILD_TIME=${BUILD_TIME}

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py .
COPY alembic.ini .
COPY requirements.txt .
COPY CHANGELOG.md .
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY static/ ./static/

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check using /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the unified entry point
CMD ["python", "-u", "main.py"]