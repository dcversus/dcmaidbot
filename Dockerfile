# Multi-stage build for smaller final image
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System build dependencies are only required while installing wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

ARG GIT_COMMIT=unknown
ARG IMAGE_TAG=latest
ARG BUILD_TIME=unknown

ENV GIT_COMMIT=${GIT_COMMIT} \
    IMAGE_TAG=${IMAGE_TAG} \
    BUILD_TIME=${BUILD_TIME}

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        wget \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /opt/venv /opt/venv

COPY --chown=app:app bot.py ./
COPY --chown=app:app bot_webhook.py ./
COPY --chown=app:app database.py ./
COPY --chown=app:app version.txt ./
COPY --chown=app:app CHANGELOG.md ./
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app handlers/ ./handlers/
COPY --chown=app:app middlewares/ ./middlewares/
COPY --chown=app:app models/ ./models/
COPY --chown=app:app services/ ./services/
COPY --chown=app:app tools/ ./tools/
COPY --chown=app:app static/ ./static/
COPY --chown=app:app config/ ./config/
COPY --chown=app:app conftest.py ./

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["sh", "-c", "if [ \"$WEBHOOK_MODE\" = \"true\" ]; then python -u bot_webhook.py; else python -u bot.py; fi"]
