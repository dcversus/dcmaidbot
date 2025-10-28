"""
Status service for monitoring bot health and deployment information.

Provides:
- Version and changelog information
- System runtime information
- Database and Redis status (when available)
- Deployment information (git commit, image tag, build time)
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class StatusService:
    """Service for retrieving bot status and health information."""

    def __init__(self, db_engine: Optional[AsyncEngine] = None):
        """Initialize status service with start time.

        Args:
            db_engine: Optional database engine for health checks
        """
        self.start_time = datetime.now(timezone.utc)
        self.db_engine = db_engine

    def get_version_info(self) -> dict:
        """Get version and changelog information.

        Returns:
            dict: Version information including version, changelog,
                  git commit, and image tag
        """
        version = self._read_version_file()
        changelog = self._read_changelog()

        return {
            "version": version,
            "changelog": changelog,
            "git_commit": os.getenv("GIT_COMMIT", "unknown"),
            "image_tag": os.getenv("IMAGE_TAG", "latest"),
            "build_time": os.getenv("BUILD_TIME", "unknown"),
        }

    def get_system_info(self) -> dict:
        """Get system runtime information.

        Returns:
            dict: System information including uptime, Python version, environment
        """
        uptime = datetime.now(timezone.utc) - self.start_time

        return {
            "current_time_utc": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
            "python_version": sys.version.split()[0],
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "pod_name": os.getenv("HOSTNAME", "unknown"),
            "namespace": os.getenv("POD_NAMESPACE", "prod-core"),
        }

    async def get_database_status(self) -> dict:
        """Get PostgreSQL database status.

        Returns:
            dict: Database connection status and basic stats
        """
        if not self.db_engine:
            return {
                "connected": False,
                "status": "not_configured",
                "message": "Database engine not initialized",
            }

        try:
            # Test database connection with a simple query
            async with self.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            return {
                "connected": True,
                "status": "healthy",
                "message": "PostgreSQL connected",
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "message": f"Database connection failed: {str(e)[:100]}",
            }

    async def get_redis_status(self) -> dict:
        """Get Redis connection and cache status.

        Returns:
            dict: Redis connection status and basic stats
        """
        try:
            from services.redis_service import redis_service

            if redis_service.redis:
                # Test Redis connection
                await redis_service.redis.ping()
                return {
                    "connected": True,
                    "status": "healthy",
                    "message": "Redis connected",
                }
            else:
                return {
                    "connected": False,
                    "status": "not_configured",
                    "message": "Redis not configured (optional)",
                }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "message": f"Redis connection failed: {str(e)[:100]}",
            }

    async def get_full_status(self) -> dict:
        """Get complete status information.

        Returns:
            dict: Complete status including version, system, database, and Redis info
        """
        return {
            "version_info": self.get_version_info(),
            "system_info": self.get_system_info(),
            "database": await self.get_database_status(),
            "redis": await self.get_redis_status(),
        }

    def _read_version_file(self) -> str:
        """Read version from version.txt.

        Returns:
            str: Version string or 'unknown' if file not found
        """
        try:
            with open("version.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "unknown"
        except (IOError, OSError) as e:
            return f"error: {e}"

    def _read_changelog(self, lines: int = 30) -> str:
        """Read recent changelog entries.

        Args:
            lines: Number of lines to read from changelog

        Returns:
            str: Changelog content or error message
        """
        try:
            with open("CHANGELOG.md", "r") as f:
                changelog_lines = f.readlines()
                return "".join(changelog_lines[:lines])
        except FileNotFoundError:
            return "Changelog not available"
        except (IOError, OSError) as e:
            return f"Error reading changelog: {e}"

    async def get_health_status(self) -> tuple[bool, dict]:
        """Get health status for Kubernetes probes.

        Returns:
            tuple: (is_healthy: bool, status_details: dict)
        """
        # Check database and Redis status
        db_status = await self.get_database_status()
        redis_status = await self.get_redis_status()

        # Determine check statuses
        db_check = (
            "ok"
            if db_status["connected"]
            else "unavailable"
            if db_status["status"] == "not_configured"
            else "error"
        )
        redis_check = (
            "ok"
            if redis_status["connected"]
            else "unavailable"
            if redis_status["status"] == "not_configured"
            else "error"
        )

        # Bot is healthy if it's running and either:
        # - Database is connected, or
        # - Database is not configured (optional)
        # Redis is always optional
        is_healthy = db_check in ["ok", "unavailable"]

        return is_healthy, {
            "status": "healthy" if is_healthy else "unhealthy",
            "checks": {
                "bot": "ok",
                "database": db_check,
                "redis": redis_check,
            },
        }
