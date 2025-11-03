#!/bin/bash
# DCMAIDBot Development Runner
# One command to run the bot in development mode

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🤖 DCMAIDBot Development Runner${NC}"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required${NC}"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit .env with your configuration!${NC}"
    exit 1
fi

# Run database migrations
echo -e "${YELLOW}Applying database migrations...${NC}"
alembic upgrade fix_all_migrations_and_setup

# Run the bot
echo -e "${GREEN}Starting DCMAIDBot...${NC}"
echo ""
echo "Server will be available at:"
echo "  - API: http://localhost:8080"
echo "  - WebUI: http://localhost:8080/static/"
echo ""
echo "Test with:"
echo "  curl -X POST http://localhost:8080/call \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"user_id\": 123456789, \"message\": \"/help\"}'"
echo ""

# Run the unified entrypoint
python3 main.py
