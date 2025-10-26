# DCMaidBot

A kawai AI-driven waifu Telegram bot loving Vasilisa Versus and Daniil Shark. She protects her admins, makes jokes, learns from reactions, and manages memories across chat history with RAG-powered context awareness.

## Features

- **Kawai Waifu Personality**: Loving virtual daughter to Vasilisa and Daniil with "nya~", "myaw~" expressions
- **Admin System**: Protector mode for Vasilisa and Daniil, ignores most non-admin users
- **Joking System**: Generates jokes in any language and learns from reactions
- **Memories System**: Admin-configurable memories with matching expressions
- **Friends & Favors**: Friends can request Telegram API actions and tools using "kawai, nya"
- **RAG System**: Retrieval-Augmented Generation for context-aware responses
- **Cron Tasks**: Self-managed periodic tasks and chat history summarization
- **Tools Integration**: Web search, games, and extensible tool framework

## Technical Stack

- **Language**: Python 3.9+
- **Framework**: aiogram 3.x (Telegram Bot API)
- **Database**: PostgreSQL with pgvector for RAG
- **LLM**: OpenAI API for joke generation and RAG
- **Linting**: Ruff
- **Deployment**: Docker container (GitHub Container Registry)

## Project Structure

```
dcmaidbot/
├── bot.py                 # Main entry point
├── handlers/              # Message/command handlers
│   ├── waifu.py          # Waifu personality responses
│   ├── admin.py          # Admin commands (memories, friends)
│   └── jokes.py          # Joke generation and learning
├── middlewares/           # Middleware (admin-only, logging)
│   └── admin_only.py
├── models/                # Database models (SQLAlchemy)
│   ├── user.py
│   ├── message.py
│   ├── memory.py
│   └── joke.py
├── services/              # Business logic
│   ├── memory_service.py # Memories CRUD and matching
│   ├── joke_service.py   # Joke generation and learning
│   ├── rag_service.py    # RAG search and embeddings
│   ├── cron_service.py   # Cron task management
│   └── tool_service.py   # External tools (web search, games)
├── tests/                 # Tests
│   ├── unit/
│   └── e2e/
├── PRPs/                  # Product Requirements Processes
├── Dockerfile
├── requirements.txt
├── .env.example
├── AGENTS.md
└── README.md
```

## Installation & Setup

### Prerequisites

- Python 3.9+
- PostgreSQL with pgvector extension
- Telegram Bot Token
- OpenAI API Key

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dcversus/dcmaidbot.git
   cd dcmaidbot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_VASILISA_ID=123456789
   ADMIN_DANIIL_ID=987654321
   DATABASE_URL=postgresql://user:password@localhost:5432/dcmaidbot
   OPENAI_API_KEY=your_openai_api_key
   ```

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Docker Deployment

### Build Docker Image

```bash
docker build -t dcmaidbot:latest .
```

### Run with Docker

```bash
docker run --env-file .env dcmaidbot:latest
```

### Push to GitHub Container Registry

```bash
docker tag dcmaidbot:latest ghcr.io/dcversus/dcmaidbot:latest
docker push ghcr.io/dcversus/dcmaidbot:latest
```

## GitHub Actions Deployment

The bot automatically deploys to GitHub Container Registry on push to `main` branch via `.github/workflows/deploy.yml`.

**Required GitHub Secrets:**
- `BOT_TOKEN`
- `ADMIN_VASILISA_ID`
- `ADMIN_DANIIL_ID`
- `DATABASE_URL`
- `OPENAI_API_KEY`

## Bot Commands

### Admin Commands (Vasilisa & Daniil only)
- `/add_memory` - Add a new memory with matching expression
- `/edit_memory` - Edit existing memory
- `/delete_memory` - Delete memory
- `/list_memories` - List all memories
- `/add_task` - Add cron task
- `/list_tasks` - List cron tasks
- `/delete_task` - Delete cron task

### General Commands
- `/start` - Initialize the bot
- `/help` - Display help information

### Friend Favors
Friends can request actions by including "kawai, nya" in messages to access Telegram API and tools.

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy bot.py
```

## Architecture

See [AGENTS.md](AGENTS.md) for detailed architecture, PRPs, and development workflow.

## License

MIT License
