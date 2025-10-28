# Simplified single-stage build for reliability
FROM python:3.13-slim

# Build arguments for deployment information
ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

# Set as environment variables
ENV GIT_COMMIT=${GIT_COMMIT}
ENV IMAGE_TAG=${IMAGE_TAG}
ENV BUILD_TIME=${BUILD_TIME}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY bot_webhook.py .
COPY database.py .
COPY version.txt .
COPY CHANGELOG.md .
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY handlers/ ./handlers/
COPY middlewares/ ./middlewares/
COPY models/ ./models/
COPY services/ ./services/
COPY static/ ./static/
COPY conftest.py .

# Create non-root user and set ownership
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Health check using /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Expose webhook port
EXPOSE 8080

# Run bot in webhook mode if WEBHOOK_MODE=true, else polling
CMD ["sh", "-c", "if [ \"$WEBHOOK_MODE\" = \"true\" ]; then python -u bot_webhook.py; else python -u bot.py; fi"]
