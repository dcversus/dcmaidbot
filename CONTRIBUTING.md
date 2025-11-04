# Contributing to DCMAIDBot

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (connects to dev instance in Kubernetes cluster)
- Redis (for caching and lessons storage)
- OpenAI API key (for LLM features and testing)

### Setup

1. **Clone and run**:
```bash
git clone <repository-url>
cd dcmaidbot
./run.sh
```

That's it! The `run.sh` script handles:
- Virtual environment creation
- Dependencies installation
- Database migrations
- Server startup

### Manual Setup

If you prefer manual setup:

1. **Environment**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing tools
```

2. **Configuration**:
```bash
cp .env.example .env
# Edit .env with your settings including OPENAI_API_KEY
```

3. **Database**:
```bash
alembic upgrade head
```

4. **Run**:
```bash
python3 main.py
```

## Testing with LLM Judge Integration

### Overview
DCMAIDBot uses an advanced testing strategy with AI-powered evaluation:
- **E2E Tests**: Real user journey validation
- **LLM Judge**: AI evaluates test quality and business value
- **Historical Tracking**: Compares results across runs
- **Release Quality**: Assesses readiness against CHANGELOG.md

### Running Tests Locally

#### Quick Test Commands
```bash
# Run all tests with rich output
source .env && python3 run_e2e_tests.py

# Run only the comprehensive conversation journey
pytest tests/e2e/test_comprehensive_conversation_journey.py -v -s

# Run only the status check test
pytest tests/e2e/test_status_check.py -v -s

# Run business/DoD validation tests
pytest tests/business/dod_validation/ -v

# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html
```

#### Test Server Setup
Tests require a running test server:

```bash
# Start test server in background
source .env && DATABASE_URL=sqlite+aiosqlite:///./test.db \
  python3 run_test_server.py &

# Run tests
pytest tests/e2e/ -v

# Clean up
pkill -f run_test_server.py
```

### Understanding Test Results

#### LLM Judge Verdict Format
```
============================================================
🤖 LLM JUDGE VERDICT
============================================================
Score: 0.85/1.0
Confidence: 0.90
Verdict: ✅ PASS

✅ Strengths:
  • Natural conversation flow
  • Proper memory retention
  • Good emotional responses

⚠️  Weaknesses:
  • Minor delay in tool responses

💡 Recommendations:
  • Optimize web search response time
  • Add more edge case testing
============================================================
```

#### Score Interpretation
- **0.9-1.0**: Excellent - Ready for production
- **0.7-0.89**: Good - Minor improvements needed
- **0.5-0.69**: Fair - Significant improvements needed
- **<0.5**: Poor - Not ready for production

### CI/CD Integration

#### Automatic PR Comments
When you create a PR, the CI workflow:
1. Runs all E2E tests with LLM Judge
2. Calculates overall score (weighted average)
3. Comments on the PR with detailed results
4. Fails if score < 0.70

#### Score Weights
- Comprehensive Journey: 40%
- Status Check: 30%
- Business/DoD Tests: 30%

#### Historical Tracking
- Results are stored in `.github/test-history/`
- Trends are analyzed across runs
- Regressions are automatically detected

### Test Structure

#### E2E Tests (3 Core Tests)
1. **Comprehensive Conversation Journey** (`tests/e2e/test_comprehensive_conversation_journey.py`)
   - Single long conversation covering all features
   - Tests memory, lessons, VAD, mood, tools
   - Includes optional LLM Judge evaluation

2. **Status Check** (`tests/e2e/test_status_check.py`)
   - Validates status endpoint and thoughts generation
   - Polls for version, self-check, crypto thoughts
   - Assesses system health with LLM analysis

3. **Platform Integration Manual** (`tests/e2e/test_platform_integration_manual.py`)
   - Manual TG/Discord testing
   - Requires human confirmation at each step

#### Business/DoD Tests
- Located in `tests/business/dod_validation/`
- Validate specific PRP requirements
- Focus on business outcomes, not implementation

### Writing Good Tests

#### Test Behavior, Not Implementation
```python
# Good: Tests user experience
async def test_user_can_retrieve_memories():
    response = await call_bot("/memories", user_id, is_admin=True)
    assert "memories found" in response["response"]

# Bad: Tests internal service calls
async def test_memory_service_called():  # Don't do this
    pass
```

#### Use Realistic Data
```python
# Good: Realistic user message
"Hi! I'm Sarah, a data scientist from San Francisco"

# Bad: Unhelpful test data
"test message 123"
```

### Pre-Commit Checklist

Before committing:
1. [ ] Run `pytest tests/ -v` - all tests pass
2. [ ] Run `ruff check . && ruff format .` - code quality
3. [ ] Update CHANGELOG.md if needed
4. [ ] Verify OPENAI_API_KEY is set for LLM Judge
5. [ ] Check test coverage >80%

### Release Process

#### Before Release
1. Ensure all tests pass with score >0.70
2. Verify CHANGELOG.md is updated
3. Run manual platform integration tests
4. Review LLM Judge recommendations

#### Post-Release
1. Monitor LLM Judge scores in production
2. Track trends over time
3. Address any regressions immediately

### Debugging Test Failures

#### Common Issues

**Server Connection Failed**
```bash
# Check if test server is running
curl -s http://localhost:8000/health

# Restart if needed
pkill -f run_test_server.py
python3 run_test_server.py &
```

**OpenAI API Key Not Set**
```bash
# Set the API key
export OPENAI_API_KEY=your_key_here

# Or add to .env file
echo "OPENAI_API_KEY=your_key_here" >> .env
```

**Low LLM Judge Confidence**
- Review test logs for context
- Check if test covers actual business value
- Verify test isn't too synthetic
- Add more realistic user scenarios

### Advanced Features

#### Historical Analysis
The LLM Judge tracks results over time:
- Detects score improvements/degradations
- Identifies flaky tests
- Recommends areas for improvement

#### Release Quality Assessment
- Reads CHANGELOG.md entries
- Validates test coverage of new features
- Assesses risk level (LOW/MEDIUM/HIGH)
- Provides release readiness score

#### Enhanced Prompts
The LLM Judge uses sophisticated prompts that consider:
- Historical context
- Release requirements
- Business value assessment
- Technical quality metrics

## Development & Deployment Guide

### Development Environment

**Local Development with Kubernetes Database:**
```bash
# 1. Start port-forward to database
kubectl port-forward -n dcmaidbot dcmaidbot-postgresql-0 5432:5432

# 2. Set environment
export DATABASE_URL="postgresql+asyncpg://dcmaidbot:password@localhost:5432/dcmaidbot_dev"

# 3. Run migrations (if needed)
alembic upgrade head

# 4. Start the bot
python3 main.py
```

### Staging Environment

**Staging Deployment:**
```bash
# 1. Deploy to staging
kubectl apply -f k8s/staging/

# 2. Run migrations manually
kubectl exec -n staging deployment/dcmaidbot -- alembic upgrade head

# 3. Verify deployment
kubectl logs -n staging deployment/dcmaidbot -f
```

### Production Environment

**Production Deployment:**
```bash
# 1. Deploy without auto-migration
kubectl apply -f k8s/production/

# 2. Run migrations manually (REQUIRED)
kubectl exec -n production deployment/dcmaidbot -- alembic upgrade head

# 3. Verify deployment
kubectl logs -n production deployment/dcmaidbot -f
```

**⚠️ PRODUCTION MIGRATION RULES:**
- NEVER auto-migrate in production
- ALWAYS run migrations manually
- CHECK migration status before deployment: `alembic current`
- VERIFY with `alembic history` if unsure

## Architecture

```
dcmaidbot/
├── src/                    # All backend code
│   ├── api/               # API layer
│   │   ├── handlers/      # Request handlers
│   │   ├── middleware/    # Middleware
│   │   └── routes/        # Route definitions
│   ├── core/              # Core business logic
│   │   ├── models/        # Database models
│   │   ├── services/      # Business services
│   │   └── tools/         # LLM tools
│   ├── config/            # Configuration files
│   └── utils/             # Utilities
├── static/                # Frontend static files
├── tests/                 # Test suite
├── PRPs/                  # Product Requirements
└── main.py                # Unified entry point
```

## Development Modes

The bot automatically detects the appropriate mode based on environment variables:

### 1. Production Webhook Mode
Set `WEBHOOK_URL` to your webhook URL:
```env
WEBHOOK_URL=https://yourdomain.com/webhook
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://...
```

### 2. Development Webhook Mode
Set `BOT_TOKEN` but not `WEBHOOK_URL`:
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://...
# No WEBHOOK_URL set
```

### 3. API-Only Mode
Don't set `BOT_TOKEN`:
```env
DATABASE_URL=postgresql+asyncpg://...
# No BOT_TOKEN set
```

## Migration Management

### Simple Migration Commands

```bash
# Check current status
alembic current

# Check what needs to be done
alembic history

# Run migrations (when ready)
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

### Environment-Specific Rules

| Environment | Auto-Migrate | Command |
|-------------|---------------|---------|
| Local Dev | ✅ Yes | `alembic upgrade head` |
| Staging | ✅ Yes | `alembic upgrade head` |
| Production | ❌ NO | `kubectl exec -- alembic upgrade head` |

### Migration Error Handling

The bot will fail fast with clear error messages if migrations are needed:

```
❌ DATABASE MIGRATION REQUIRED
===============================================
Current database revision: a027e3b9e6eb
Latest migration revision: c3f3ebfc3d19

Please run migrations before starting the bot:

    alembic upgrade head

Or in Kubernetes:

    kubectl exec -n <namespace> <pod-name> -- alembic upgrade head
===============================================
```

## Code Style

### Linting and Formatting
```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Testing

### Run Tests
```bash
# All tests
pytest tests/ -v

# E2E tests
pytest tests/e2e/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=src --cov-report=html
```

### Test API Endpoint
```bash
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456789, "message": "/help"}'
```

## Key Features

### Memory System with Emotional Intelligence
- **Multi-CoT Analysis**: 4-chain-of-thought emotional processing
- **VAD Emotions**: Valence-Arousal-Dominance tracking
- **Memory Commands**: `/mood`, `/memories`, `/memorize`, `/relate`
- **Relationship Tracking**: Trust, friendship, familiarity metrics
- **Admin Protection**: Admin messages always have positive impact

### Tools Integration
- Memory management (create, search, retrieve)
- Web search via DuckDuckGo
- Lesson management (admin only)
- External tool execution with access control

## Environment Variables

### Required
- `DATABASE_URL` - Database connection string (PostgreSQL only)
- `ADMIN_IDS` - Comma-separated admin Telegram IDs

### Optional
- `BOT_TOKEN` - Telegram bot token
- `OPENAI_API_KEY` - OpenAI API key for LLM
- `REDIS_URL` - Redis connection for caching
- `WEBHOOK_URL` - Webhook URL for production
- `NUDGE_SECRET` - Secret for /nudge endpoint

### Development
- `DATABASE_DEBUG=true` - Enable SQL query logging
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8080)
- `SKIP_MIGRATION_CHECK=true` - Skip migration check (dev only)

## Adding New Features

### 1. Create a Tool
Add tools in `src/core/tools/`:

```python
# src/core/tools/my_tool.py
MY_TOOL = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }
    }
}
```

### 2. Add a Command
Add commands in `src/api/handlers/`:

```python
# src/api/handlers/my_command.py
from aiogram import Router
from aiogram.filters import Command

router = Router()

@router.message(Command("mycommand"))
async def cmd_mycommand(message):
    await message.reply("Hello!")
```

### 3. Add a Service
Create services in `src/core/services/`:

```python
# src/core/services/my_service.py
class MyService:
    def __init__(self, session):
        self.session = session

    async def do_something(self):
        pass
```

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "Description"
```

### Apply Migration
```bash
# Development/Staging
alembic upgrade head

# Production (MANUAL ONLY)
kubectl exec -it deployment/dcmaidbot -- alembic upgrade head
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs
```bash
tail -f logs/dcmaidbot.log
```

## Performance

### Redis Caching
Enable Redis for better performance:
```env
REDIS_URL=redis://localhost:6379
```

### Database Pooling
The bot uses SQLAlchemy async connection pooling automatically.

## Deployment

### Docker
```bash
# Build
docker build -t dcmaidbot .

# Run (development)
docker run -p 8080:8080 -e DATABASE_URL="postgresql+asyncpg://..." dcmaidbot

# Run (production with migrations)
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e BOT_TOKEN="..." \
  dcmaidbot
```

### Kubernetes
```yaml
# Production deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmaidbot
spec:
  template:
    spec:
      containers:
      - name: dcmaidbot
        image: dcmaidbot:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dcmaidbot-secrets
              key: database-url
        # NO AUTO-MIGRATE IN PRODUCTION
```

### Systemd
Create a service file at `/etc/systemd/system/dcmaidbot.service`.

## Troubleshooting

### Migration Issues
If migrations fail:
1. Check database connection: `psql $DATABASE_URL`
2. Run migrations manually: `alembic upgrade head`
3. Check for stuck migrations: `alembic history`

### Permission Issues
Ensure ADMIN_IDS includes your Telegram ID for admin features.

### Import Errors
Run with `PYTHONPATH=src python3 main.py` if imports fail.

## Code Review Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Submit a pull request

## Community

- Report bugs via GitHub issues
- Discuss features in pull requests
- Join our Discord (link in README)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
