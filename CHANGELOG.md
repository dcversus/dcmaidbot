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
- **PRP-013: Production E2E Testing with Test Bot**
  - Automated production testing design using separate test bot
  - Real Telegram API calls to verify deployed features
  - Smoke tests and full regression test suite
  - GitHub Actions integration for post-deploy verification

### Changed
- Migrated from Vercel to GitHub Container Registry
- Completely rewrote README.md for waifu bot architecture
- Updated .env.example with new required variables
- Deploy workflow reads version.txt and creates GitHub releases
- **Downgraded Python from 3.14-slim to 3.13-slim** (hotfix for pydantic-core build issue)

### Fixed
- **CRITICAL: Added bot_webhook.py to Docker image** (emergency fix for production crash)
  - Dockerfile CMD referenced bot_webhook.py but file was not copied
  - Caused all pods to enter CrashLoopBackOff state
  - Fixed by adding COPY bot_webhook.py to Dockerfile
- **Enhanced CONTRIBUTING.md with pre-commit workflow**
  - Automated quality checks before commits
  - Step-by-step setup instructions
  - Pre-commit hook testing guide

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
