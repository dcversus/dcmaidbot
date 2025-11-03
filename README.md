# DCMAIDBot

An AI-powered Telegram assistant with emotional intelligence, memory management, and multi-chain-of-thought analysis. The bot features advanced emotional tracking, relationship management, and context-aware responses.

## 🌟 Key Features

### Emotional Intelligence
- **Multi-CoT Analysis**: 4-chain-of-thought emotional processing
- **VAD Emotion Tracking**: Valence-Arousal-Dominance emotional state
- **Mood-Aware Responses**: Bot's tone adapts based on current emotional state
- **Relationship Evolution**: Tracks trust, friendship, and familiarity with users

### Memory Management
- **Automatic Memory Creation**: Learns from conversations
- **Categorized Storage**: 35+ memory categories across 6 domains
- **Memory Linking**: Create connections between related memories
- **Search & Retrieval**: Quick access to stored information

### Commands
- `/mood` - Check bot's current emotional state
- `/memories` - View stored memories (role-based access)
- `/memorize <text>` - Explicitly save information
- `/relate <id1> <id2>` - Link memories together
- `/help` - Show available commands

### Admin Protection
- Admin messages always have positive impact
- Protected from negative mood swings
- Enhanced access control and management features

## 🏗️ Architecture

```
dcmaidbot/
├── src/                    # All backend code
│   ├── api/               # API layer (handlers, middleware, routes)
│   ├── core/              # Core business logic
│   │   ├── models/        # Database models
│   │   ├── services/      # Business services
│   │   ├── tools/         # LLM tools
│   │   └── utils/         # Utilities
│   └── config/            # Configuration files
├── static/                # Frontend static files
├── tests/                 # Test suite
├── PRPs/                  # Product Requirements
├── main.py                # Unified entry point
└── run.sh                 # Development runner
```

## 🚀 Quick Start

### One-Command Setup
```bash
git clone <repository-url>
cd dcmaidbot
./run.sh
```

That's it! The bot will:
1. Create a virtual environment
2. Install dependencies
3. Apply database migrations
4. Start the server on port 8080

### Manual Setup
```bash
# 1. Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# Edit .env with your settings

# 3. Database
alembic upgrade head

# 4. Run
python3 main.py
```

## 🎯 Development Modes

The bot automatically detects the appropriate mode:

### 1. Production Webhook Mode
```env
WEBHOOK_URL=https://yourdomain.com/webhook
BOT_TOKEN=your_bot_token
```

### 2. Development Webhook Mode
```env
BOT_TOKEN=your_bot_token
# No WEBHOOK_URL - runs webhook server locally
```

### 3. API-Only Mode
```env
# No BOT_TOKEN - API endpoints only
DATABASE_URL=postgresql://...
```

## 📡 API Testing

Test the bot without Telegram using the `/call` endpoint:

```bash
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456789, "message": "/help"}'
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# E2E tests with LLM judge
pytest tests/e2e/ -v --llm-judge

# Code quality
ruff check .
ruff format .
mypy src/
```

## 🔧 Configuration

### Required Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `ADMIN_IDS` - Comma-separated admin Telegram IDs

### Optional Variables
- `BOT_TOKEN` - Telegram bot token
- `OPENAI_API_KEY` - OpenAI API key
- `REDIS_URL` - Redis connection for caching
- `WEBHOOK_URL` - Webhook URL (production)
- `NUDGE_SECRET` - Secret for /nudge endpoint

## 🐳 Docker

```bash
# Build
docker build -t dcmaidbot .

# Run
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -e BOT_TOKEN=... \
  dcmaidbot
```

## 📚 Documentation

- [Contributing Guide](CONTRIBUTING.md) - Development setup and guidelines
- [PRPs](PRPs/) - Product Requirements Processes
- [API Documentation](docs/api.md) - API reference

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with aiogram 3.x for Telegram Bot API
- Powered by OpenAI GPT models
- Uses SQLAlchemy for database ORM
- Emotional intelligence based on VAD model research
