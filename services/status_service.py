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
from datetime import datetime


class StatusService:
    """Service for retrieving bot status and health information."""

    def __init__(self):
        """Initialize status service with start time."""
        self.start_time = datetime.utcnow()

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
        uptime = datetime.utcnow() - self.start_time

        return {
            "current_time_utc": datetime.utcnow().isoformat(),
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
        # Placeholder - will be implemented when database is set up (PRP-003/005)
        return {
            "connected": False,
            "status": "not_implemented",
            "message": "Database integration pending (PRP-003/005)",
        }

    async def get_redis_status(self) -> dict:
        """Get Redis connection and cache status.

        Returns:
            dict: Redis connection status and basic stats
        """
        # Placeholder - will be implemented when Redis is deployed (PRP-001)
        return {
            "connected": False,
            "status": "not_implemented",
            "message": "Redis integration pending (PRP-001)",
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
        except Exception:
            return "error"

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
        except Exception:
            return "Error reading changelog"

    def get_health_status(self) -> tuple[bool, dict]:
        """Get health status for Kubernetes probes.

        Returns:
            tuple: (is_healthy: bool, status_details: dict)
        """
        # For now, always healthy if service is running
        # Will check database/Redis when implemented
        return True, {
            "status": "healthy",
            "checks": {"bot": "ok", "database": "pending", "redis": "pending"},
        }
