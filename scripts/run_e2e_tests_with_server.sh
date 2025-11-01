#!/bin/bash
# Auto-start dev server and run E2E tests for pre-commit hook
# This script ensures all endpoints are tested with LLM as judge

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}PRE-COMMIT E2E TEST SUITE${NC}"
echo -e "${YELLOW}============================================${NC}"

# Check if .env file exists and load it
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. E2E tests require bot configuration.${NC}"
    exit 1
fi

# Load environment variables from .env
echo -e "${YELLOW}📋 Loading environment variables from .env...${NC}"
set -a  # Export all variables
source .env
set +a  # Stop exporting

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY not set in .env file. E2E tests require OpenAI API for LLM judge.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables loaded${NC}"

# Override DATABASE_URL to use SQLite for testing (avoid PostgreSQL permission issues)
export DATABASE_URL="sqlite+aiosqlite:///./test_e2e.db"
echo -e "${YELLOW}📦 Using SQLite for E2E tests (test_e2e.db)${NC}"

# Note: We skip Alembic migrations for SQLite tests
# The test fixtures (conftest.py) use Base.metadata.create_all() which creates
# tables directly from models (using Integer PK) instead of migrations (which use BigInteger PK)
# This avoids SQLite autoincrement issues with BigInteger
echo -e "${YELLOW}📋 Tables will be created by test fixtures (no migrations needed for SQLite)${NC}"

# Function to check if server is ready
wait_for_server() {
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            return 0
        fi

        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ Server failed to start after 30 seconds${NC}"
    return 1
}

# Function to cleanup on exit
cleanup() {
    if [ ! -z "$SERVER_PID" ]; then
        echo -e "${YELLOW}🛑 Stopping dev server (PID: $SERVER_PID)...${NC}"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Server stopped${NC}"
    fi

    # Clean up test database
    if [ -f "test_e2e.db" ]; then
        echo -e "${YELLOW}🗑️  Removing test database...${NC}"
        rm -f test_e2e.db test_e2e.db-shm test_e2e.db-wal
        echo -e "${GREEN}✅ Test database removed${NC}"
    fi
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Start the dev server in background
echo -e "${YELLOW}🚀 Starting dev server...${NC}"
DISABLE_TG=true python3 bot_webhook.py > /tmp/dcmaidbot_e2e.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
if ! wait_for_server; then
    echo -e "${RED}Server logs:${NC}"
    tail -50 /tmp/dcmaidbot_e2e.log
    exit 1
fi

# Run E2E tests
echo -e "${YELLOW}🧪 Running E2E tests with LLM judge...${NC}"
echo ""

# Run all tests marked with requires_openai (includes E2E + LLM judge tests)
if pytest -m "requires_openai" -v --tb=short --color=yes; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}✅ ALL E2E TESTS PASSED${NC}"
    echo -e "${GREEN}============================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}❌ E2E TESTS FAILED${NC}"
    echo -e "${RED}============================================${NC}"
    echo -e "${YELLOW}Server logs:${NC}"
    tail -100 /tmp/dcmaidbot_e2e.log
    exit 1
fi
