# Contributing to DCMAIDBot

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (recommended) or SQLite (for development)
- Redis (optional, for caching)

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
```

2. **Configuration**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Database**:
```bash
alembic upgrade head
```

4. **Run**:
```bash
python3 main.py
```

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
```

### 2. Development Webhook Mode
Set `BOT_TOKEN` but not `WEBHOOK_URL`:
```env
BOT_TOKEN=your_bot_token
# No WEBHOOK_URL set
```

### 3. API-Only Mode
Don't set `BOT_TOKEN`:
```env
# No BOT_TOKEN set
DATABASE_URL=postgresql://...
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
- `DATABASE_URL` - Database connection string
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
alembic upgrade head
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
docker build -t dcmaidbot .
docker run -p 8080:8080 dcmaidbot
```

### Systemd
Create a service file at `/etc/systemd/system/dcmaidbot.service`.

## Troubleshooting

### Migration Issues
If migrations fail, check:
1. Database connection in DATABASE_URL
2. PostgreSQL extensions (pgvector is optional)

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
