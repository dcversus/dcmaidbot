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
- Admin-only middleware for Vasilisa and Daniil
- Comprehensive test suite (9 tests)
- DEPLOYMENT.md with complete kubectl and GitOps instructions
- INIT_DEPLOYMENT.md with step-by-step first deployment guide
- Telegram chat import capability in PRP-004
- CLAUDE.md as symlink to AGENTS.md
- Version management with version.txt and CHANGELOG.md
- **PR #15 to uz0/core-charts with Helm charts** (updated with health probes)
- **PRP-011: Canary deployment & sister bot communication system**
- CONTRIBUTING.md with complete contribution guide
- Infrastructure workflow documentation in AGENTS.md

### Changed
- Migrated from Vercel to GitHub Container Registry
- Completely rewrote README.md for waifu bot architecture
- Updated .env.example with new required variables
- Deploy workflow reads version.txt and creates GitHub releases

### Removed
- All Vercel infrastructure (api/, vercel.json, package.json)
- Old pool management code (pool_service.py, old handlers)
- Redis dependency (preparing for PostgreSQL migration)

## [0.1.0] - 2025-10-26

### Added
- Initial project setup
- Basic bot structure with aiogram 3.x
- Development environment configuration
