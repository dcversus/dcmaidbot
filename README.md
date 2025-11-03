# DCMaidBot

A kawai AI-driven waifu Telegram bot with mysterious origins. She protects her beloved admins, makes jokes, learns from reactions, and manages memories across chat history with RAG-powered context awareness.

## Features

- **Kawai Waifu Personality**: Loving virtual daughter to her creators with "nya~", "myaw~" expressions
- **Admin System**: Protector mode for the special ones, ignores most non-admin users
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
   ADMIN_IDS=123456789
   # Add more IDs: ADMIN_IDS=123,456,789
   DATABASE_URL=postgresql://user:password@localhost:5432/dcmaidbot
   OPENAI_API_KEY=your_openai_api_key
   # Optional: point to a compatible API instead of api.openai.com
   # OPENAI_BASE_URL=https://custom-openai.example.com/v1
   # Optional: override model IDs when using non-standard providers
   # TEST_MODEL=gpt-4o-mini
   # DEFAULT_MODEL=gpt-4o-mini
   # COMPLEX_MODEL=gpt-4o
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

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster with kubectl configured
- ArgoCD for GitOps (recommended)

### Quick Deployment

1. **Create namespace and secrets:**
```bash
kubectl create namespace dcmaidbot
kubectl create secret generic dcmaidbot-secrets \
  --namespace=dcmaidbot \
  --from-literal=bot-token='YOUR_BOT_TOKEN' \
  --from-literal=admin-ids='123456789,987654321' \
  --from-literal=database-url='postgresql://user:password@postgres:5432/dcmaidbot' \
  --from-literal=openai-api-key='sk-...'
```

2. **Deploy via GitOps (Recommended):**
   - GitOps repository: https://github.com/uz0/core-charts
   - Chart location: `charts/dcmaidbot/`
   - ArgoCD automatically syncs and deploys

3. **Update version:**
```bash
# In uz0/core-charts repo
cd charts/dcmaidbot
echo 'image:
  tag: "0.2.0"' > prod.tag.yaml
git commit -am "Update dcmaidbot to v0.2.0"
git push
```

### Monitoring

```bash
# Check status
kubectl get pods -n dcmaidbot
kubectl logs -n dcmaidbot -l app=dcmaidbot -f

# Restart
kubectl rollout restart deployment/dcmaidbot -n dcmaidbot
```

## CI/CD

The bot automatically builds and pushes to GitHub Container Registry (`ghcr.io/dcversus/dcmaidbot`) on push to `main` branch.

## Bot Commands

### Admin Commands (Admins only)
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

## Development Workflow

We follow a structured PRP (Product Requirements Process) workflow with role-based responsibilities:

### Quick Overview

1. **Branch per PRP**: Each PRP gets its own branch (`prp-016-feature-name`)
2. **Implement & Test**: Write code, add tests, lint/format
3. **Create PR**: Submit PR with CHANGELOG update
4. **Review & Merge**: Address review comments, merge when approved
5. **Post-Release**: Monitor deployment, run E2E tests, verify version
6. **QC Sign-Off**: Quality Control Engineer approves post-release checklist
7. **Next PRP**: Immediately start next PRP

### Roles

- **Developer**: Implementation, testing, code review
- **QC Engineer**: Post-release verification and quality sign-off
- **SRE**: Deployment monitoring and incident response
- **DevOps Engineer**: Infrastructure and GitOps
- **Tech Writer**: Documentation

See [AGENTS.md](AGENTS.md) for complete workflow details, role responsibilities, incident management, and post-release procedures.

## Architecture

See [AGENTS.md](AGENTS.md) for detailed architecture, PRPs, and development workflow.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for full details.

## Contact

- Email: dcversus@gmail.com
- Repository: https://github.com/dcversus/dcmaidbot

---

*Nyaa~ Thank you for respecting privacy! 💕*
