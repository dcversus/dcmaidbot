# Optimized multi-stage Docker build for dcmaidbot
FROM python:3.13-slim AS builder

# Build arguments
ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

# Environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage - minimal runtime
FROM python:3.13-slim

# Build args
ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

# Environment variables
ENV PYTHONPATH=/app/src:/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_COMMIT=${GIT_COMMIT} \
    IMAGE_TAG=${IMAGE_TAG} \
    BUILD_TIME=${BUILD_TIME}

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && groupadd -r appuser \
    && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (optimize copy order for layer caching)
COPY --chown=appuser:appuser main.py run.sh alembic.ini requirements.txt CHANGELOG.md ./
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser .dockerignore ./

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Make run.sh executable
RUN chmod +x /app/run.sh

# Run the application using run.sh in production mode
CMD ["/app/run.sh", "prod"]
