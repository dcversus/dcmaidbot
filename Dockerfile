# Simplified single-stage build for reliability
FROM python:3.13-slim

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
COPY handlers/ ./handlers/
COPY middlewares/ ./middlewares/
COPY models/ ./models/
COPY services/ ./services/
COPY conftest.py .

# Create non-root user and set ownership
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose webhook port
EXPOSE 8080

# Run bot in webhook mode if WEBHOOK_MODE=true, else polling
CMD ["sh", "-c", "if [ \"$WEBHOOK_MODE\" = \"true\" ]; then python -u bot_webhook.py; else python -u bot.py; fi"]
