# Changelog

All notable changes to DCMaidBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **E2E Production Validation System**
  - tests/e2e_production.py: Comprehensive post-release testing script
  - Tests all user stories with real Telegram API calls
  - GitHub Actions workflow for automated E2E testing
  - Auto-runs after each deployment to verify production health
  - Manual trigger via workflow_dispatch

### Changed
- **Removed /version endpoint** - version info now only on landing page (/)
- Health endpoint remains at /health for Kubernetes probes

### Removed
- /version endpoint (consolidated into landing page)

## [0.3.0] - 2025-10-29

### Added
- **PRP-006: Advanced Memory Features (Relations, Versioning, Compaction)**
  - Memory versioning: create new versions without deleting originals
  - Enhanced MemoryLink model with created_by field for tracking
  - LLM-powered relation strength scoring (0.0-1.0 scale)
  - LLM-powered relation reasoning generation
  - Automatic memory compaction when approaching 4000 token limit
  - create_memory_version() method in MemoryService
  - get_memory_versions() method for version history
  - create_enhanced_link() with automatic strength and reason calculation
  - calculate_relation_strength() in LLM service
  - generate_relation_reason() in LLM service
  - compact_memory() in LLM service
  - Database migration adding created_by to memory_links
- **PRP-005 Phase 1: Enhanced Memory Database Layer**
  - Memory model with VAD (Valence-Arousal-Dominance) emotional dimensions
  - Zettelkasten-inspired attributes: keywords, tags, temporal/situational context
  - Memory versioning and evolution tracking (parent_id, evolution_triggers)
  - 6-domain categorical system (self, social, knowledge, interest, episode, meta)
  - 35 predefined categories across all domains with importance ranges
  - MemoryLink model for Zettelkasten-style bidirectional memory connections
  - SQLite/PostgreSQL compatibility with conditional ARRAY type handling
  - Category seeding script for initial database setup
  - Database migration adding all VAD and Zettelkasten fields
- **PRP-005 Phase 2: Memory Service Layer**
  - MemoryService with full CRUD operations for memories
  - Memory search with filters (category, importance, emotions, tags)
  - Memory link management (create, query bidirectional links)
  - Category management (by domain, by full_path)
  - Redis caching for frequently accessed memories
  - VAD emotion extraction from text using LLM (extract_vad_emotions)
  - Zettelkasten attribute generation using LLM (generate_zettelkasten_attributes)
  - Dynamic memory link suggestion using LLM (suggest_memory_links)
- **PRP-005 Phase 3: Comprehensive Unit Tests**
  - 14 unit tests for MemoryService covering all operations
  - CRUD operations: create, get, update, delete
  - Search operations: by query, importance, emotion
  - Memory link tests: create, query outgoing/incoming
  - Category management tests
  - Access tracking validation
  - Multi-category assignment tests
- **PRP-005 Phase 4: E2E Integration Tests**
  - 5 E2E tests for complete memory lifecycle
  - LLM-integrated VAD emotion extraction test
  - LLM-integrated Zettelkasten generation test
  - LLM-suggested dynamic memory linking test
  - Full lifecycle test (create, search, update, link, delete)
  - Multi-filter advanced search test
  - Total test count: 86 (67 original + 14 unit + 5 E2E)
- **Rich Telegram Bot UX improvements**
  - HTML formatting for all bot messages (bold, italic, code, spoilers)
  - Inline keyboards for interactive buttons (/start, /joke commands)
  - Callback query handlers for button interactions
  - Typing indicators before LLM responses (send_chat_action)
  - Bot commands menu (setMyCommands API integration)
  - Version and commit hash display in /status and /help commands
  - Website link buttons in commands (https://dcmaidbot.theedgestory.org)
- **Joke system enhancements**
  - Inline keyboard for joke reactions (😂 Funny!, 😐 Meh, 💡 Tell another!)
  - Spoiler tags for joke punchlines
  - Callback handlers for reaction tracking (foundation for PRP-006)
- **Streaming LLM responses with realistic interaction**
  - OpenAI streaming API integration for real-time response generation
  - Realistic human-like delays: read time (0.3-0.8s) + think time (0.2-0.5s)
  - Continuous typing indicators during streaming (refreshed every 5s)
  - Blazing fast response delivery as tokens arrive
  - Mimics natural conversation flow: read → think → type → send

### Changed
- All message responses now use HTML parse_mode instead of Markdown
- /start command now includes interactive buttons
- /help command displays version and git commit
- /status command shows uptime, version, commit, and site link
- /joke command uses spoiler tags and reaction buttons
- LLM service now streams responses instead of waiting for complete generation
- Message handler implements realistic interaction timing
- Bot commands menu automatically configured on startup

### Fixed
- Python 3.9 compatibility: Changed `int | None` to `Optional[int]` in models
- SQLAlchemy Table redefinition: Added `extend_existing=True` to association tables
- Memory model type annotations for Python 3.9 compatibility
- ARRAY type compatibility with SQLite via JSON serialization and proper type casting

### Technical
- **No Linter Suppression Rule** (PRP-005)
  - Documented in AGENTS.md as mandatory coding standard
  - Prohibits use of `# noqa`, `# type: ignore`, or any linter suppression
  - Enforces proper fixes for all lint/type errors

## [0.2.0] - 2025-10-28

### Added
- **Real-time database health checks** in StatusService
  - `get_database_status()` now actually tests PostgreSQL connection with `SELECT 1`
  - `get_redis_status()` now tests Redis connection with `ping()`
  - Database engine passed to StatusService initialization
  - Async health check implementation
- **Improved health endpoint** (`/health`)
  - Returns actual database connection status (ok/unavailable/error)
  - Returns actual Redis connection status (ok/unavailable/error)
  - Proper HTTP 503 response when database connection fails
  - Differentiate between not_configured and error states
- **Enhanced `/version` status page**
  - Database status shows "PostgreSQL connected" when healthy
  - Redis status shows proper connection state
  - Visual indicators (✅/⏳/❌) reflect real service status

### Changed
- `get_health_status()` is now async and performs actual health checks
- Health handler awaits `get_health_status()` for real-time status
- Database health considered critical (bot unhealthy if DB error)
- Redis health considered optional (bot healthy even if Redis unavailable)

### Fixed
- Health endpoint no longer shows "pending" for working PostgreSQL connection
- Proper error messages when database connection fails
- Status page now accurately reflects production service health

## [0.1.0] - 2025-10-28

### Added
- PRP-001: Infrastructure cleanup and GitHub Container Registry deployment
- Multi-stage Dockerfile for optimized production builds
- GitHub Actions workflow for GHCR deployment
- AGENTS.md with core goal and 10 PRPs
- Initial waifu personality handler
- Admin-only middleware for beloved admins
- Comprehensive test suite (9 tests)
- Kubernetes deployment guide in README.md and PRP-001
- Documentation rules in AGENTS.md (5 allowed locations only)
- Telegram chat import capability in PRP-004
- CLAUDE.md as symlink to AGENTS.md
- Version management with version.txt and CHANGELOG.md
- **PR #15 to uz0/core-charts with Helm charts** (updated with health probes)
- **PRP-011: Canary deployment & sister bot communication system**
- CONTRIBUTING.md with complete contribution guide
- Infrastructure workflow documentation in AGENTS.md
- Claude Code GitHub Actions workflow for AI-powered code assistance
- Pre-commit configuration with ruff linter and formatter hooks
- **PRP-003: PostgreSQL database foundation (11 tests passing)**
  - User, Message, Fact, Stat models with SQLAlchemy
  - Alembic migrations for database versioning
  - Async database connection with connection pooling
  - Linear message history for RAG
  - Bilingual support (ru/en) in messages
- **PRP-012: Analytics & Observability framework**
  - Research completed on LangSmith, Prometheus, Grafana
  - Comprehensive analytics requirements defined
  - Privacy-first approach with GDPR compliance
- **PRP-013: Status & Monitoring Dashboard** ✨
  - `/version` endpoint with beautiful kawai HTML status page
  - `/health` endpoint for Kubernetes liveness/readiness probes
  - Build metadata pipeline: GitHub Actions → Docker → ENV vars
  - Version, git commit, image tag, and build timestamp tracking
  - System runtime info: uptime, Python version, environment, pod name
  - Graceful handling for pending services (database/Redis)
  - Responsive terminal theme design with emoji indicators (⏳ ✅ ❌)
  - Recent changelog display from CHANGELOG.md
- **PRP-014: Agent-to-User Communication via /nudge Endpoint** 🤖
  - `/nudge` POST endpoint for async agent-to-admin communication
  - NudgeService for forwarding requests to external LLM endpoint
  - Authentication via NUDGE_SECRET stored in Kubernetes secrets
  - Request validation (user_ids, message, optional PR/PRP links)
  - External endpoint forwarding to dcmaid.theedgestory.org/nudge
  - Complete MANDATORY autonomous workflow system in AGENTS.md
  - Emotional intelligence guidelines for PRP progress comments
  - 6-phase execution workflow (selection → implementation → PR → deploy → loop)
  - User feedback loop with async /nudge communication pattern
- **PRP-015: Lilit's Room - Interactive Chibi Anime Landing Page** 💕
  - Beautiful kawaii landing page served at `/` (root path)
  - Serious hero section with GitHub links and installation guide
  - Interactive widget grid representing Lilit's room (top-down view)
  - Live widgets: Real-time clock, version display, uptime, service status
  - Visual novel-style changelog stories (click widgets to read)
  - Funny backstories for each release (The Birth, The Little Sister, The Seed)
  - Chibi anime aesthetic with pastel colors and cute animations
  - Responsive grid layout with hover effects and smooth transitions
  - Service status widgets: Redis (paper desk), PostgreSQL (bookshelf), Bot (smartphone)
  - Decorative widgets: Cactus, The Edge Story ad, future GameBoy Pong placeholder
  - Modal system for interactive storytelling
  - Complete PRP-015 documentation with 11-day implementation plan
- **PRP-002: LLM Agent Framework with BASE_PROMPT & LESSONS** 🤖💡
  - OpenAI GPT-4o-mini integration for intelligent bot responses
  - BASE_PROMPT system: Configurable personality from config/base_prompt.txt
  - LESSONS system: Admin-only secret instructions injected into every LLM call
  - Redis caching for lessons (3600s TTL)
  - PostgreSQL persistence for lessons with Alembic migration
  - Admin commands: /view_lessons, /add_lesson, /edit_lesson, /remove_lesson, /reorder_lesson
  - LLM service with OpenAI function calling support
  - Tool registry framework for extensible bot capabilities
  - Lesson model with order, active status, timestamps
  - Automatic lesson injection in all LLM responses
  - Bilingual support (русский + English) in LLM context
  - Unit tests for LLM service and lesson service (14 tests)
  - E2E tests for LLM integration with lessons (2 tests)
  - Redis service with graceful fallback (bot works without Redis)

### Changed
- Migrated from Vercel to GitHub Container Registry
- Completely rewrote README.md for waifu bot architecture
- Updated .env.example with new required variables (added REDIS_URL)
- **PRP-002: Transformed bot into intelligent LLM-powered agent**
  - Waifu handler now uses LLM service for all non-command messages
  - Only responds to admins (99% ignore rule enforced)
  - Lessons automatically loaded from database and injected into context
  - Redis connection initialized on bot startup
- Deploy workflow reads version.txt and creates GitHub releases
- **Downgraded Python from 3.14-slim to 3.13-slim** (hotfix for pydantic-core build issue)
- **Enhanced CONTRIBUTING.md with pre-commit workflow**
  - Automated quality checks before commits
  - Step-by-step setup instructions
  - Pre-commit hook testing guide
- **PRP-013: Enhanced deployment pipeline with metadata tracking**
  - bot_webhook.py: Register /version and /health monitoring endpoints
  - Dockerfile: Accept GIT_COMMIT, IMAGE_TAG, BUILD_TIME build args as ENV vars
  - deploy.yml: Pass build metadata to Docker during CI/CD
- **PRP-015: Moved main landing page from `/version` to `/`**
  - Old status page still available at `/version` for monitoring
  - New kawaii landing page is now the main entry point
  - Dockerfile updated to include static/ directory for assets

### Fixed
- **CRITICAL: Added bot_webhook.py to Docker image** (emergency fix for production crash)
  - Dockerfile CMD referenced bot_webhook.py but file was not copied
  - Caused all pods to enter CrashLoopBackOff state
  - Fixed by adding COPY bot_webhook.py to Dockerfile

### Removed
- All Vercel infrastructure (api/, vercel.json, package.json)
- Old pool management code (pool_service.py, old handlers)
- Redis dependency (preparing for PostgreSQL migration)
- **Temporary documentation files** (INIT_DEPLOYMENT.md, LEGEND.md, DEPLOYMENT.md, PHASE_*_STATUS.md, PRIVACY_CLEANUP_SUMMARY.md, VERIFICATION.md, WAITING_FOR_REVIEW.md)
  - Content consolidated into PRPs and README.md
  - Enforcing strict documentation location policy

## [0.1.0] - 2025-10-26 🎉 WEEKEND CELEBRATION!

### Added
- Initial project setup
- Basic bot structure with aiogram 3.x
- Development environment configuration
