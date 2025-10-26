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

### Changed
- Migrated from Vercel to GitHub Container Registry
- Completely rewrote README.md for waifu bot architecture
- Updated .env.example with new required variables

### Removed
- All Vercel infrastructure (api/, vercel.json, package.json)
- Old pool management code (pool_service.py, old handlers)
- Redis dependency (preparing for PostgreSQL migration)

## [0.1.0] - 2025-10-26

### Added
- Initial project setup
- Basic bot structure with aiogram 3.x
- Development environment configuration
