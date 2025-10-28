# Changelog

All notable changes to DCMaidBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **PRP-016: Multi-Room Interactive House Exploration - Phase 1** 🎮
  - Welcome Modal with first-visit greeting and GitHub Stars widget
  - Complete music system architecture with BGM player and sound effects
  - Music toggle button (top-right, fixed position)
  - 6 contextual sound effects (hover, click, tick-tock, cactus, status, pop)
  - Interactive widget click actions:
    - Version widget → CHANGELOG.md navigation
    - Commit widget → GitHub commit page navigation
    - Uptime widget → Grow animation + tooltip
    - Redis/PostgreSQL widgets → Status modal with external links
    - Bot Status widget → Telegram bot link
  - Status modal system for service information display
  - Widget animations (grow, pulse-glow, fade-in)
  - Dynamic tooltip system
  - Audio placeholders with comprehensive sourcing documentation
  - localStorage persistence for user music preference
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

### Changed
- Migrated from Vercel to GitHub Container Registry
- Completely rewrote README.md for waifu bot architecture
- Updated .env.example with new required variables
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
