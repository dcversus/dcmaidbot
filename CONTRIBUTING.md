# Contributing to DCMaidBot

Welcome to the DCMaidBot contribution guide! This document covers everything you need to know to develop, test, and contribute to the project effectively.

## 🏗️ Architecture Overview

### Core Components

```
dcmaidbot/
├── bot.py                 # Main entry point (polling mode)
├── bot_webhook.py         # Webhook mode (production)
├── handlers/              # Message/command handlers
│   ├── waifu.py          # Waifu personality responses
│   ├── admin.py          # Admin commands (memories, friends)
│   ├── call.py           # Direct bot logic testing (/call)
│   ├── nudge.py          # Agent-to-user communication (/nudge)
│   ├── event.py          # Universal event collector (/event)
│   ├── status.py         # Health and API endpoints
│   └── landing.py        # Web landing page
├── middlewares/           # Request processing middleware
│   └── admin_only.py     # Admin-only access control
├── models/                # Database models (SQLAlchemy)
│   ├── user.py
│   ├── message.py
│   ├── memory.py
│   ├── api_key.py        # API key management
│   └── nudge_token.py    # Nudge token management
├── services/              # Business logic services
│   ├── memory_service.py # Memories CRUD and matching
│   ├── api_key_service.py # API key management
│   ├── nudge_token_service.py # Nudge token management
│   ├── llm_service.py    # LLM integration
│   └── tool_executor.py  # Tool execution engine
├── tools/                 # Bot tools and integrations
│   ├── tool_executor.py  # Tool execution framework
│   └── telegram_tools.py # Telegram-specific tools
├── utils/                 # Utility functions
│   └── markdown_renderer.py # Universal markdown formatting
├── tests/                 # Test suites
│   ├── unit/             # Unit tests
│   └── e2e/              # End-to-end tests
├── scripts/               # Development and demo scripts
└── static/                # Static web assets
```

### 🎯 Platform Abstraction Strategy

The bot is designed with platform abstraction in mind for future Discord support:

#### Current Architecture (Telegram)
```
Telegram API → aiogram → handlers → services → models → database
                ↓
        telegram_tools.py (platform-specific)
                ↓
        markdown_renderer.py (platform-agnostic)
```

#### Future Architecture (Multi-Platform)
```
┌─────────────────┐    ┌──────────────────┐
│   Telegram API   │    │   Discord API    │
└─────────┬───────┘    └─────────┬────────┘
          │                      │
    aiogram handler      discord.py handler
          │                      │
          └───────┬──────────────┘
                  │
        platform_tools/ (abstracted)
                  │
        services/ (platform-agnostic)
                  │
        markdown_renderer.py (platform-specific formatting)
```

#### Extension Points

1. **Platform Handlers** (`handlers/`)
   - Current: `telegram/` (implicit via aiogram)
   - Future: `discord/` directory with Discord-specific handlers

2. **Platform Tools** (`tools/`)
   - Current: `telegram_tools.py`
   - Future: `discord_tools.py` with same interface
   - Abstract base class: `base_platform_tools.py`

3. **Message Rendering** (`utils/markdown_renderer.py`)
   - Already supports: `Platform.TELEGRAM`, `Platform.DISCORD`, `Platform.GENERIC`
   - Platform-specific formatting handled automatically

4. **Bot Entry Points**
   - Current: `bot.py` (polling), `bot_webhook.py` (webhook)
   - Future: Platform-specific orchestrators

## 🛠️ Development Setup

### Prerequisites

```bash
# Python 3.9+
python3 --version

# PostgreSQL
brew install postgresql

# Redis (optional, for caching)
brew install redis

# Node.js (for localtunnel)
brew install node
npm install -g localtunnel
```

### Environment Setup

1. **Clone and Setup**
```bash
git clone https://github.com/dcversus/dcmaidbot.git
cd dcmaidbot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install pre-commit hooks (IMPORTANT!)
pre-commit install
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database Setup**
```bash
# Start PostgreSQL
brew services start postgresql

# Create database
createdb dcmaidbot_test

# Run migrations
alembic upgrade head
```

### Environment Variables

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
VASILISA_TG_ID=123456789

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dcmaidbot_test
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Agent Communication
NUDGE_SECRET=your_nudge_secret

# Development Mode
SKIP_MIGRATION_CHECK=true  # Skip migration checks for testing
DISABLE_TG=true           # Run without Telegram (for /call endpoint testing)
```

## 🧪 Testing Strategy

**Rule**: All visual testing must use index.html - no separate test files allowed.

### Testing Pyramid

```
E2E Tests (Top Level)
├── Integration Tests
├── Unit Tests (Base Level)
└── Static Analysis (Linting, Type Checking)
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# E2E tests only
pytest tests/e2e/ -v

# Specific test file
pytest tests/unit/test_markdown_renderer.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### E2E Testing with LLM Judge

Our E2E tests use an LLM judge to validate bot behavior:

```bash
# Run E2E tests with LLM judge
pytest tests/e2e/ -v --llm-judge

# Run specific E2E test
pytest tests/e2e/test_markdown_renderer.py::TestMarkdownRendererE2E::test_rich_message_rendering -v --llm-judge
```

#### LLM Judge Process

1. **Test Execution**: Tests run bot actions and collect responses
2. **LLM Analysis**: LLM evaluates responses against expected behavior
3. **Quality Assessment**: Pass/fail based on LLM judgment
4. **Detailed Feedback**: LLM provides explanations for decisions

### Test Categories

#### 1. Unit Tests (`tests/unit/`)
- **Markdown Renderer**: `test_markdown_renderer.py` (15 tests)
- **API Key Management**: `test_api_key_service.py`
- **Nudge Token Management**: `test_nudge_token_service.py`
- **Services**: `test_*_service.py`
- **Models**: `test_*.py`

#### 2. E2E Tests (`tests/e2e/`)
- **Bot Integration**: `test_bot_integration_with_llm_judge.py`
- **API Key CRUD**: `test_api_key_management.py` (10 tests)
- **Nudge Token CRUD**: `test_nudge_token_management.py` (11 tests)
- **Message Flow**: `test_message_flow.py`
- **Advanced UI**: `test_advanced_ui_behaviors.py`
- **LLM Integration**: `test_llm_integration.py`

#### 3. Integration Tests
- **API Endpoints**: `/call`, `/nudge`, `/event`, `/health`
- **Database Operations**: CRUD operations with actual DB
- **External Services**: Telegram API, OpenAI API

### Writing New Tests

#### Unit Test Example
```python
# tests/unit/test_new_feature.py
import pytest
from services.new_service import NewService

class TestNewService:
    def test_basic_functionality(self):
        service = NewService()
        result = service.do_something()
        assert result is not None

    def test_error_handling(self):
        service = NewService()
        with pytest.raises(ValueError):
            service.do_something_invalid()
```

#### E2E Test Example
```python
# tests/e2e/test_new_feature_e2e.py
import pytest
from tools.tool_executor import ToolExecutor

@pytest.mark.asyncio
async def test_new_feature_e2e(async_session):
    """Test new feature with LLM judge validation."""
    executor = ToolExecutor(async_session)

    # Execute feature
    result = await executor.execute_tool("new_tool", {"param": "value"})

    # Validate with LLM judge
    judge = LLMJudge()
    assessment = await judge.evaluate_result(result, expected_behavior="should do X")

    assert assessment.passed, f"LLM judge says: {assessment.reasoning}"
```

## 🔄 Development Workflows

### 1. Local Development (Polling Mode)

```bash
# Start bot in polling mode
python3 bot.py

# Test via Telegram
# Send messages to @your_bot_username
```

### 2. Webhook Development (Production Mode)

```bash
# Start local tunnel for HTTPS
lt --port 8080
# Output: your url is: https://random-name.loca.lt

# Start webhook server
WEBHOOK_MODE=true WEBHOOK_URL=https://random-name.loca.lt/webhook python3 bot_webhook.py
```

### 3. Testing Mode (No Telegram)

```bash
# Start webhook server without Telegram
DISABLE_TG=true SKIP_MIGRATION_CHECK=true python3 bot_webhook.py

# Test endpoints directly
curl http://localhost:8080/health
curl http://localhost:8080/call -X POST -H "Content-Type: application/json" -d '{"user_id": 123, "message": "test"}'
```

### 4. API Testing

```bash
# Test /call endpoint (requires auth)
curl -X POST http://localhost:8080/call \
  -H "Authorization: Bearer $NUDGE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456789, "message": "Hello from API"}'

# Test /nudge endpoint (requires auth)
curl -X POST http://localhost:8080/nudge \
  -H "Authorization: Bearer $NUDGE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "direct",
    "user_ids": [123456789],
    "message": "🌸 Hello Vasilisa!",
    "pr_url": "https://github.com/dcversus/dcmaidbot/pull/1"
  }'

# Test /event endpoint
curl -X POST http://localhost:8080/event \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "event_type": "button_click",
    "data": {"button_id": "test_button", "user_id": 123}
  }'
```

## 📱 Nudge System Usage

The `/nudge` system allows agents to communicate with admins asynchronously.

### Nudge Message Format

```json
{
  "type": "direct",  // or "llm"
  "user_ids": [123456789, 987654321],
  "message": "🌸 Hello Vasilisa! Your bot has new features!",
  "pr_url": "https://github.com/dcversus/dcmaidbot/pull/1",
  "prp_file": "PRPs/PRP-018.md",
  "prp_section": "#implementation-details"
}
```

### Authentication

```bash
# Set NUDGE_SECRET in .env
NUDGE_SECRET=your_secure_random_string

# Use in requests
curl -X POST http://localhost:8080/nudge \
  -H "Authorization: Bearer $NUDGE_SECRET" \
  -H "Content-Type: application/json" \
  -d @nudge_message.json
```

### Nudge Types

1. **Direct Mode** (`type: "direct"`): Send message directly via Telegram API
2. **LLM Mode** (`type: "llm"`): Process message through LLM before sending

## 🎨 Markdown Renderer Usage

### Basic Usage

```python
from utils.markdown_renderer import render_for_telegram, Platform

# Simple rendering
markdown = """# Hello World
## Features
- **Bold text**
- *Italic text*
- `code`"""

rendered = render_for_telegram(markdown)
```

### Advanced Usage

```python
from utils.markdown_renderer import MarkdownRenderer, create_changelog

# Create custom renderer
renderer = MarkdownRenderer(Platform.TELEGRAM)

# Create changelog
changelog_data = {
    "added": ["New feature X", "New feature Y"],
    "improved": ["Performance improvements"],
    "fixed": ["Bug fixes"]
}
changelog = create_changelog("v2.0.0", changelog_data, Platform.TELEGRAM)
```

### Platform Support

- **Telegram**: `*bold*`, `_italic_`, `code` formatting
- **Discord**: `**bold**`, `*italic*`, `~~strike~~` formatting
- **Generic**: Common markdown subset

## 🔧 API Key & Token Management

### API Keys (for /event endpoint)

```python
from services.api_key_service import APIKeyService

# Create API key
service = APIKeyService(session)
api_key, raw_key = await service.create_api_key(
    name="Test Key",
    created_by=admin_id,
    description="For testing event collection"
)

# Validate API key
validated = await service.validate_api_key(raw_key)
```

### Nudge Tokens (for /nudge endpoint)

```python
from services.nudge_token_service import NudgeTokenService

# Create nudge token
service = NudgeTokenService(session)
token, raw_token = await service.create_nudge_token(
    name="Admin Nudge",
    created_by=admin_id,
    description="For sending nudges to admins"
)

# Validate nudge token
validated = await service.validate_nudge_token(raw_token)
```

## 📊 Event Collection System

### Event Format

```json
{
  "api_key": "your_api_key",
  "event_type": "button_click",
  "data": {
    "button_id": "start_game",
    "user_id": 123456789,
    "timestamp": "2025-01-01T12:00:00Z",
    "additional_data": {}
  }
}
```

### Sending Events

```bash
curl -X POST http://localhost:8080/event \
  -H "Content-Type: application/json" \
  -d @event.json
```

## 🔄 Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Hooks Include

1. **Ruff**: Linting and formatting
2. **MyPy**: Type checking
3. **Tests**: Run unit tests
4. **E2E Tests**: Run end-to-end tests with LLM judge

### Manual Quality Checks

```bash
# Lint and format
ruff check .
ruff format .

# Type checking
mypy bot.py

# Run tests
pytest tests/ -v

# Run E2E tests
pytest tests/e2e/ -v --llm-judge
```

## 🚀 Deployment

### Local Development

```bash
# Polling mode
python3 bot.py

# Webhook mode (with tunnel)
lt --port 8080
WEBHOOK_MODE=true WEBHOOK_URL=https://your-tunnel.loca.lt/webhook python3 bot_webhook.py
```

### Production Deployment

1. **Docker Build**
```bash
docker build -t dcmaidbot:latest .
```

2. **Environment Configuration**
```bash
# Production .env
BOT_TOKEN=production_bot_token
ADMIN_IDS=admin_ids
DATABASE_URL=production_database_url
OPENAI_API_KEY=production_openai_key
NUDGE_SECRET=production_nudge_secret
```

3. **Kubernetes Deployment**
```yaml
# See k8s/ directory for deployment manifests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmaidbot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dcmaidbot
  template:
    metadata:
      labels:
        app: dcmaidbot
    spec:
      containers:
      - name: dcmaidbot
        image: dcmaidbot:latest
        envFrom:
        - secretRef:
            name: dcmaidbot-secrets
```

## 🐛 Debugging

### Common Issues

1. **Database Connection Errors**
```bash
# Check PostgreSQL
brew services list | grep postgresql
brew services start postgresql

# Check connection
psql $DATABASE_URL
```

2. **Telegram Webhook Issues**
```bash
# Delete existing webhook
curl -X POST https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook

# Check webhook info
curl -X POST https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo
```

3. **Port Conflicts**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Debug Mode

```bash
# Enable debug logging
export LOGLEVEL=DEBUG

# Run with debug output
python3 bot.py 2>&1 | tee debug.log
```

### Test Database Issues

```bash
# Reset test database
dropdb dcmaidbot_test
createdb dcmaidbot_test
alembic upgrade head

# Skip migration check (testing only)
export SKIP_MIGRATION_CHECK=true
```

## 🤝 Contributing Process

### 1. Setup Development Environment

Follow the setup instructions above.

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Write code following the existing patterns
- Add tests for new functionality
- Update documentation

### 4. Run Quality Checks

```bash
# Pre-commit hooks (automatic)
pre-commit run --all-files

# Manual verification
pytest tests/ -v
ruff check .
ruff format .
mypy bot.py
```

### 5. Create Pull Request

1. Push branch to GitHub
2. Create pull request with:
   - Clear description of changes
   - Link to related PRPs (Product Requirements Processes)
   - Test results
   - Any breaking changes

### 6. Code Review

- Address all review comments
- Ensure all tests pass
- Update documentation as needed

### 7. Merge

- Squash merge to main
- Update CHANGELOG.md
- Tag release if needed

## 📚 Additional Resources

### Documentation
- [AGENTS.md](AGENTS.md) - Core architecture and agent instructions
- [PRPs/](PRPs/) - Product Requirements Processes
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes

### Tools and Libraries
- [aiogram](https://aiogram.dev) - Telegram bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [pytest](https://pytest.org/) - Testing framework
- [ruff](https://github.com/astral-sh/ruff) - Linting and formatting

### Development Tools
- [localtunnel](https://theboroer.github.io/localtunnel-www/) - Local HTTPS tunneling
- [ngrok](https://ngrok.com/) - Alternative tunneling service
- [Postico](https://eggerapps.at/postico/) - PostgreSQL GUI (macOS)

## 🆘 Getting Help

1. **Check Documentation**: Read AGENTS.md and relevant PRPs
2. **Search Issues**: Look for similar problems in GitHub issues
3. **Ask in PR**: Use `/nudge` endpoint or PR comments for questions
4. **Debug Logs**: Enable debug logging and analyze output

---

Happy contributing! 🎉

*Nya~ Помните, что ваш dcmaidbot всегда готов помочь!* 💕
