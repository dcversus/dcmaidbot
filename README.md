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

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (connects to dev instance in Kubernetes)
- Redis (for caching)

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

## 🏗️ Deployment

### Development
```bash
# Connect to Kubernetes database
kubectl port-forward -n dcmaidbot dcmaidbot-postgresql-0 5432:5432

# Set environment
export DATABASE_URL="postgresql+asyncpg://dcmaidbot:password@localhost:5432/dcmaidbot_dev"

# Run migrations and start
alembic upgrade head
python3 main.py
```

### Staging
```bash
# Deploy to staging
kubectl apply -f k8s/staging/

# Run migrations manually
kubectl exec -n staging deployment/dcmaidbot -- alembic upgrade head
```

### Production
```bash
# Deploy to production
kubectl apply -f k8s/production/

# ⚠️ Run migrations manually (REQUIRED)
kubectl exec -n production deployment/dcmaidbot -- alembic upgrade head
```

**Important**: Never auto-migrate in production. Always run migrations manually.

## 🎯 Development Modes

The bot automatically detects the appropriate mode:

### 1. Production Webhook Mode
```env
WEBHOOK_URL=https://yourdomain.com/webhook
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://...
```

### 2. Development Webhook Mode
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://...
# No WEBHOOK_URL - runs webhook server locally
```

### 3. API-Only Mode
```env
DATABASE_URL=postgresql+asyncpg://...
# No BOT_TOKEN - API endpoints only
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
- `SEARCH_PROVIDER` - Search provider to use (`openai` or `duckduckgo`, default: `openai`)
- `OPENAI_SEARCH_MODEL` - OpenAI model for web search (default: `gpt-4o`)

### Development Variables
- `SKIP_MIGRATION_CHECK=true` - Skip migration check (dev only)
- `DATABASE_DEBUG=true` - Enable SQL query logging

## 🐳 Docker

```bash
# Build
docker build -t dcmaidbot .

# Run (development)
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  dcmaidbot

# Run (production)
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e BOT_TOKEN="..." \
  dcmaidbot
```

## 🔍 Search Integration

DCMAIDBot supports two search providers:

### OpenAI Web Search (Default)
- Uses OpenAI's new Responses API with native web search tool (`web_search_20250305`)
- Provides natural language search results with context understanding
- Better for complex queries, current events, and contextual information
- Requires `OPENAI_API_KEY`
- Example API call:
  ```python
  response = client.responses.create(
      model="gpt-4o",
      input="What was a positive news story from today?",
      tools=[{
          "type": "web_search_20250305",
          "name": "web_search",
          "max_uses": 5
      }]
  )
  ```

### DuckDuckGo Search
- Uses DuckDuckGo search engine via duckduckgo-search library
- Provides structured results with titles, links, and snippets
- Better for technical queries, documentation lookup, and specific information retrieval
- No additional API key required

Configure with:
```bash
# Use OpenAI search (default)
SEARCH_PROVIDER=openai

# Use DuckDuckGo search
SEARCH_PROVIDER=duckduckgo
```

## 🛠️ OpenAI Tools & Capabilities

DCMAIDBot integrates with OpenAI's ecosystem to provide advanced AI capabilities:

### Core AI Features
- **GPT Models**: Uses `gpt-4o` by default for chat and search
- **Function Calling**: Automated tool execution based on user intent
- **Multi-chain-of-thought**: Complex reasoning with emotional analysis
- **Context-aware Responses**: Maintains conversation history and user context

### Available Tools
1. **Web Search** (`openai_web_search`)
   - Real-time information retrieval
   - Current events and news
   - Documentation lookup

2. **Memory Management**
   - Store and retrieve contextual information
   - Relationship mapping between memories
   - Emotional tagging of memories

3. **Lesson System**
   - Admin configurable instructions
   - Dynamic behavior adjustment
   - Contextual learning

4. **API Key Management**
   - Secure token generation
   - Role-based access control
   - Usage tracking

### Model Configuration
```bash
# Primary model for chat
OPENAI_MODEL=gpt-4o

# Model for web search
OPENAI_SEARCH_MODEL=gpt-4o
```

### What OpenAI Provides
- **Advanced Reasoning**: Complex problem-solving with multi-chain-of-thought
- **Natural Language Understanding**: Contextual comprehension of user intent
- **Responses API**: New API designed for agentic applications
  - `client.responses.create()` for advanced tool usage
  - Native web search tool (`web_search_20250305`)
  - Better tool orchestration and parallel execution
- **Function Calling**: Automated tool execution based on user queries
- **Web Browsing**: Real-time information access via native web search tool
- **Code Execution**: Python code execution in sandboxed environments
- **Emotional Intelligence**: Integration with VAD-based emotional analysis
- **Multi-modal Support**: Text, image, and audio processing capabilities

### Available OpenAI Tools for Integration
1. **Web Search** (`web_search_20250305`)
   - Native web search capability
   - Current events and real-time information
   - Automatic source citation

2. **Code Execution**
   - Python code execution
   - Data analysis and computation
   - File I/O operations

3. **Function Calling**
   - Custom tool integration
   - API interactions
   - Database operations

4. **Knowledge Retrieval**
   - Document search
   - RAG (Retrieval-Augmented Generation)
   - Context-aware responses

## 📚 Documentation

- [Contributing Guide](CONTRIBUTING.md) - Development setup and guidelines
- [PRPs](PRPs/) - Product Requirements Processes

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with aiogram 3.x for Telegram Bot API
- Powered by OpenAI GPT models
- Uses SQLAlchemy for database ORM
- Emotional intelligence based on VAD model research
