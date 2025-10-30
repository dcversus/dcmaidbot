# Changelog

All notable changes to DCMaidBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **PRP-016 Phase 2: Easter Egg Discovery System** 🥚✨
  - **EasterEggManager class** - Complete easter egg tracking and discovery
    - LocalStorage persistence for found eggs across sessions
    - Progress tracking with 9 hidden easter eggs
    - Discovery notifications with bounce animations
    - Automatic state management (found vs. unfound)
  - **Easter Egg Counter UI** - Fixed position display in top-right
    - Real-time counter showing X/9 eggs found
    - Purple-to-pink gradient styling
    - Hover scale animation for engagement
  - **Discovery Notification System** - Celebratory popup on find
    - Animated bounce effect on discovery
    - 3-second auto-dismiss
    - Custom message per egg with name display
  - **9 Hidden Easter Eggs** strategically placed in Lilith's Room:
    - Lilith Meditation, Organizing, Contract
    - AI Emotion Wheel
    - Warrior Vasilisa, Casual Vasilisa
    - Comic Storyboard, Character Designs, Development Sketches
  - **Visual Effects**:
    - Grayscale + low opacity when undiscovered (pulse animation)
    - Golden glow on hover (0 0 20px rgba(255, 215, 0, 0.8))
    - Full color + opacity when found
    - Scale transform on hover for feedback
- **PRP-016 Phase 1: Interactive Landing Page Enhancement** 🎵✨
  - **Phase 1B: Music System** - Complete audio management implementation
    - AudioManager class with Web Audio API for sound effect playback
    - Background music support with loop control (30% volume)
    - Music toggle button (fixed position, top-right corner with pink gradient)
    - Graceful fallback for browsers without Web Audio API support
    - Sound placeholder system ready for audio file integration
  - **Phase 1C: Widget Click Actions** - Interactive widget behaviors
    - Clock widget: Plays tick-tock sound effect
    - Version widget: Opens CHANGELOG.md in GitHub
    - Git Commit widget: Opens specific commit page in GitHub
    - Uptime widget: Plays funny song snippet
    - Redis/PostgreSQL widgets: Opens status.theedgestory.org
    - Bot Status widget: Opens @dcmaidbot Telegram chat
    - Cactus widget: Plays funny sound effect
    - The Edge Story widget: Opens theedgestory.org website
  - **Phase 1D: Widget Hover States** - Enhanced visual feedback
    - Improved hover transform: translateY(-8px) + scale(1.02)
    - Pink gradient glow effect on hover (blur + opacity fade)
    - Pulsing radial gradient animation (2s cycle)
    - Hover sound effects (30% volume)
    - Enhanced shadow effects on widget hover
  - Future-ready audio system with placeholder paths:
    - `/static/audio/bgm-lofi-anime.mp3` (background music)
    - `/static/audio/hover.mp3` (widget hover sound)
    - `/static/audio/click.mp3` (button click sound)
    - `/static/audio/tick-tock-loop.mp3` (clock sound)
    - `/static/audio/funny-song.mp3` (cactus & uptime sound)
- **PRP-017: Role-Based Access Control & Admin Lesson Tools** 🔐
  - Created `tools/lesson_tools.py` with 4 admin-only lesson management tools
    - `get_all_lessons` - List all lessons with IDs and content
    - `create_lesson` - Add new lesson through natural conversation
    - `edit_lesson` - Update existing lesson content
    - `delete_lesson` - Remove lesson (soft delete)
  - Created `services/auth_service.py` for centralized authentication
    - `is_admin(user_id)` - Check if user has admin permissions
    - `get_role(user_id)` - Get user role ("admin" or "user")
    - `filter_tools_by_role()` - Filter tools based on user permissions
    - `is_admin_only_tool()` - Check if tool requires admin access
  - Created `handlers/help.py` with role-aware /help command
    - Admins see full command list including lesson management
    - Non-admins see only public commands
    - Different tool descriptions based on role
  - Enhanced `tools/tool_executor.py` with role-based access control
    - Admin-only tools return vague deflection for non-admins
    - "I'm not sure what you mean by that! 😊" instead of permission errors
    - Prevents leaking information about admin-only features
  - Updated `handlers/waifu.py` and `handlers/call.py`
    - Filter tools by user role before passing to LLM
    - Admins get lesson tools, non-admins don't
    - Seamless integration with existing tool system
  - Comprehensive test suite (26 tests total):
    - 10 tests for AuthService (role checking, tool filtering)
    - 16 tests for lesson tools (tool definitions, RBAC, execution)
    - All tests passing with full coverage
  - **Feature**: Admins can now manage lessons conversationally
    - "Save this as a lesson: Always be enthusiastic!"
    - "Show me all my lessons"
    - "Edit lesson #3 to say..."
    - "Delete lesson #5"
  - **Security**: Non-admins get natural deflections, no access denied errors
    - Bot doesn't reveal that lesson features exist
    - Maintains kawaii personality even when denying access

### Fixed
- **Hotfix: /nudge LLM mode parameter bug** 🐛
  - Fixed incorrect `use_tools` parameter → `tools` in `NudgeService.send_via_llm()`
  - LLM mode now works correctly with personalized messaging
  - Direct mode was unaffected (working since v0.3.0)

### Changed
- **PRP-014 v0.2.0: Direct Telegram Messaging via /nudge** 🔄
  - **BREAKING**: Removed external endpoint forwarding (dcmaid.theedgestory.org/nudge)
  - `/nudge` now sends messages DIRECTLY via Telegram Bot API
  - Two messaging modes:
    - **direct**: Send markdown-formatted message as-is
    - **llm**: Process message through dcmaidbot LLM pipeline for personalized responses
  - New request schema: `{message, type, user_id?}` (simplified)
  - Removed superfluous fields: urgency, pr_url, prp_file, prp_section
  - Messages support full Markdown formatting
  - `user_id` optional - defaults to all ADMIN_IDS
  - Updated tests: 15 handler tests + 16 service tests
  - **Why**: Original architecture was incorrect - external endpoint didn't exist

### Added
- **PRP-005 Phase 2: Agentic Tools Integration** 🤖🎊
  - Bot is now FULLY AGENTIC - can autonomously use tools!
  - `tools/memory_tools.py`: Memory management tools (create_memory, search_memories, get_memory)
  - `tools/web_search_tools.py`: Web search tool using DuckDuckGo (no API key needed)
  - `tools/tool_executor.py`: Tool execution engine with automatic VAD + Zettelkasten extraction
  - Bot autonomously creates memories when users share important information
  - Bot searches memories to recall past conversations
  - Bot searches web for current information
  - `services/llm_service.py`: Tool support with OpenAI function calling
  - `handlers/waifu.py` and `handlers/call.py`: Process tool calls from LLM
  - `tests/e2e/test_agentic_tools_with_judge.py`: Comprehensive E2E test with batch LLM judge
  - Automatic importance scoring, VAD emotion extraction, Zettelkasten attributes on memory creation
- **PRP-005 Phase 1: Memory and Message History in Bot Responses** 🎉
  - Integrated MemoryService into handlers/waifu.py - bot now fetches relevant memories
  - Integrated MessageService for message history tracking (last 20 messages)
  - Bot stores all incoming/outgoing messages to database for context
  - LLM prompts now include memories and conversation history
  - /call endpoint updated to use full context (memories + history + lessons)
  - Bot responses now contextually aware of past conversations and stored facts
- **/call endpoint - Direct bot logic testing** 🆕 **RECOMMENDED APPROACH**
  - POST /call endpoint for testing bot logic without Telegram
  - Same authentication as /nudge (NUDGE_SECRET)
  - Accepts user_id + command or message
  - Returns bot's response directly (no Telegram involved)
  - Perfect for CI/CD automation
  - tests/e2e_call_endpoint.py: Automated E2E tests via /call
  - handlers/call.py: Bot logic abstracted from Telegram
  - **Why**: Telegram bots can't message users who haven't initiated chat
  - **Solution**: Bypass Telegram entirely, test bot logic directly
- **E2E Production Validation System**
  - tests/e2e_production.py: Infrastructure and health testing
  - tests/e2e_user_stories.py: **Real user story and feature testing**
  - **tests/e2e_with_userbot.py: Automated bot-to-bot testing using Pyrogram** 🆕
    - Uses Pyrogram (MTProto) to act as a real Telegram user
    - Sends messages to bot and verifies responses
    - Solves "chat not found" error in automated tests
    - Supports session persistence (tests/userbot.session)
    - Requires Telegram API credentials (api_id, api_hash)
  - Tests ALL bot commands: /start, /help, /status, /joke, /love, /view_lessons
  - Tests LLM integration: waifu personality, streaming responses, joke generation
  - Tests memory system: PostgreSQL database, Redis caching
  - Tests /nudge endpoint for agent communication
  - GitHub Actions workflow for automated E2E testing after each deployment
  - Manual trigger via workflow_dispatch
  - 11 user story tests covering all implemented PRPs
  - **tests/README.md: Comprehensive E2E testing documentation**
- **/api/version endpoint** - Lightweight JSON API for landing page
  - Returns version, commit, uptime, service statuses
  - Used by landing page for dynamic version display
  - Replaces HTML scraping from old /version endpoint
- **Test Bot Configuration (@dcnotabot)**
  - Dedicated test bot for E2E testing
  - Stored in Kubernetes secret: dcmaidbot-test-secrets
  - GitHub Actions secrets: BOT_TOKEN, TEST_ADMIN_ID, NUDGE_SECRET
  - Local .env file for development testing
  - Automated /call endpoint E2E tests in GitHub Actions workflow

### Changed
- **Removed /version endpoint** - version info now only on landing page (/)
- Landing page now fetches live data from /api/version JSON endpoint
- Hero version badge shows "Loading..." until API response arrives
- Health endpoint remains at /health for Kubernetes probes

### Removed
- /version HTML endpoint (replaced by /api/version JSON API)

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
- **PRP-015: Lilith's Room - Interactive Chibi Anime Landing Page** 💕
  - Beautiful kawaii landing page served at `/` (root path)
  - Serious hero section with GitHub links and installation guide
  - Interactive widget grid representing Lilith's room (top-down view)
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
