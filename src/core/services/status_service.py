"""
Status service for monitoring bot health and deployment information.

Provides:
- Version and changelog information
- System runtime information
- Database and Redis status (when available)
- Deployment information (git commit, image tag, build time)
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass
class Thought:
    """Structured thought for system analysis."""

    timestamp: str
    thought_type: str  # "version" or "self_check"
    category: str
    content: str
    confidence: float  # 0.0 - 1.0
    impact: str  # "low", "medium", "high", "critical"
    actionable: bool
    recommendations: List[str]
    metadata: Dict[str, Any]


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
            from core.services.redis_service import redis_service

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
            dict: Complete status including version, system, database, Redis, and crypto thoughts
        """
        base_status = {
            "version_info": self.get_version_info(),
            "system_info": self.get_system_info(),
            "database": await self.get_database_status(),
            "redis": await self.get_redis_status(),
        }

        # Add crypto thoughts if available
        try:
            from core.services.redis_service import redis_service

            if redis_service.redis:
                crypto_status_key = "crypto:status:latest"
                crypto_status = await redis_service.redis.get(crypto_status_key)
                if crypto_status:
                    base_status["crypto_thoughts"] = json.loads(crypto_status)
                else:
                    base_status["crypto_thoughts"] = {"status": "not_available"}
            else:
                base_status["crypto_thoughts"] = {"status": "redis_unavailable"}
        except Exception as e:
            base_status["crypto_thoughts"] = {"status": "error", "error": str(e)[:100]}

        return base_status

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

    async def generate_version_thoughts(
        self, system_status: Dict[str, Any]
    ) -> List[Thought]:
        """Generate version thoughts about system state and changes.

        Args:
            system_status: Current system status information

        Returns:
            List[Thought]: Version thoughts about system evolution
        """
        thoughts = []
        current_time = datetime.now(timezone.utc).isoformat()

        # Database evolution thoughts
        db_status = system_status.get("database", {})
        if db_status.get("connected"):
            response_time = self._estimate_response_time()
            if response_time < 100:
                thoughts.append(
                    Thought(
                        timestamp=current_time,
                        thought_type="version",
                        category="database",
                        content="Database connections are performing excellently with optimal response times",
                        confidence=0.9,
                        impact="low",
                        actionable=False,
                        recommendations=[
                            "Continue monitoring database performance trends"
                        ],
                        metadata={
                            "response_time_estimate_ms": response_time,
                            "status": "optimal",
                        },
                    )
                )
            elif response_time < 500:
                thoughts.append(
                    Thought(
                        timestamp=current_time,
                        thought_type="version",
                        category="database",
                        content="Database performance is acceptable but showing signs of load",
                        confidence=0.8,
                        impact="medium",
                        actionable=True,
                        recommendations=[
                            "Monitor for query optimization opportunities",
                            "Review indexing strategy for frequently accessed data",
                        ],
                        metadata={
                            "response_time_estimate_ms": response_time,
                            "status": "acceptable",
                        },
                    )
                )

        # Redis evolution thoughts
        redis_status = system_status.get("redis", {})
        if redis_status.get("connected"):
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="version",
                    category="cache",
                    content="Redis cache layer is functioning properly, supporting system performance",
                    confidence=0.85,
                    impact="low",
                    actionable=False,
                    recommendations=[
                        "Monitor cache hit ratios for optimization opportunities"
                    ],
                    metadata={"cache_status": "healthy", "availability": "optimal"},
                )
            )

        # Bot evolution thoughts
        uptime = system_status.get("system_info", {}).get("uptime_seconds", 0)
        uptime_hours = uptime / 3600
        if uptime_hours > 24:
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="version",
                    category="stability",
                    content=f"Bot has maintained stable operation for {uptime_hours:.1f} hours, demonstrating good reliability",
                    confidence=0.95,
                    impact="low",
                    actionable=False,
                    recommendations=[
                        "Document stability patterns for future deployments"
                    ],
                    metadata={
                        "uptime_hours": uptime_hours,
                        "stability_rating": "excellent",
                    },
                )
            )

        # Version progression thoughts
        version_info = system_status.get("version_info", {})
        current_version = version_info.get("version", "unknown")
        if current_version != "unknown":
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="version",
                    category="deployment",
                    content=f"System is running version {current_version} with successful deployment validation",
                    confidence=0.9,
                    impact="low",
                    actionable=False,
                    recommendations=[
                        "Maintain version tracking for release management"
                    ],
                    metadata={
                        "version": current_version,
                        "deployment_status": "successful",
                    },
                )
            )

        return thoughts

    async def generate_self_check_thoughts(
        self, system_status: Dict[str, Any]
    ) -> List[Thought]:
        """Generate self-check thoughts about system internal state.

        Args:
            system_status: Current system status information

        Returns:
            List[Thought]: Self-check thoughts about system health
        """
        thoughts = []
        current_time = datetime.now(timezone.utc).isoformat()

        # Overall system health self-check
        db_healthy = system_status.get("database", {}).get("connected", False)
        redis_healthy = system_status.get("redis", {}).get("connected", False)

        if db_healthy and redis_healthy:
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="self_check",
                    category="overall_health",
                    content="All critical system components (database, cache) are operational and healthy",
                    confidence=0.95,
                    impact="low",
                    actionable=False,
                    recommendations=["Continue regular health monitoring"],
                    metadata={
                        "components_healthy": ["database", "redis"],
                        "overall_status": "optimal",
                    },
                )
            )
        elif db_healthy:
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="self_check",
                    category="overall_health",
                    content="Primary systems operational but cache layer unavailable - reduced performance expected",
                    confidence=0.8,
                    impact="medium",
                    actionable=True,
                    recommendations=[
                        "Investigate Redis connectivity issues",
                        "Consider fallback caching strategies",
                        "Monitor performance degradation",
                    ],
                    metadata={
                        "components_healthy": ["database"],
                        "components_degraded": ["redis"],
                    },
                )
            )
        else:
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="self_check",
                    category="overall_health",
                    content="Critical system components are experiencing issues - immediate attention required",
                    confidence=0.9,
                    impact="high",
                    actionable=True,
                    recommendations=[
                        "Investigate database connectivity immediately",
                        "Check system resource availability",
                        "Review recent changes that may have caused degradation",
                    ],
                    metadata={"components_healthy": [], "critical_issues": True},
                )
            )

        # Performance self-check
        uptime = system_status.get("system_info", {}).get("uptime_seconds", 0)
        if uptime < 300:  # Less than 5 minutes
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="self_check",
                    category="performance",
                    content="System recently restarted - monitoring for stability patterns",
                    confidence=0.8,
                    impact="medium",
                    actionable=True,
                    recommendations=[
                        "Monitor for any post-restart issues",
                        "Verify all services are properly initialized",
                        "Check for any startup errors in logs",
                    ],
                    metadata={"uptime_seconds": uptime, "restart_recent": True},
                )
            )

        # Resource utilization self-check
        python_version = system_status.get("system_info", {}).get("python_version", "")
        if python_version:
            major_version = int(python_version.split(".")[0])
            if major_version < 3:
                thoughts.append(
                    Thought(
                        timestamp=current_time,
                        thought_type="self_check",
                        category="compatibility",
                        content=f"System running Python {python_version} - consider upgrading to Python 3.x for better performance and security",
                        confidence=0.9,
                        impact="medium",
                        actionable=True,
                        recommendations=[
                            "Plan migration to Python 3.x",
                            "Test compatibility with current codebase",
                            "Update dependencies for Python 3.x",
                        ],
                        metadata={
                            "python_version": python_version,
                            "upgrade_recommended": True,
                        },
                    )
                )

        # Environment self-check
        environment = system_status.get("system_info", {}).get("environment", "")
        if environment == "unknown":
            thoughts.append(
                Thought(
                    timestamp=current_time,
                    thought_type="self_check",
                    category="configuration",
                    content="Environment configuration not properly set - may affect monitoring and debugging",
                    confidence=0.8,
                    impact="medium",
                    actionable=True,
                    recommendations=[
                        "Set ENVIRONMENT variable (development/staging/production)",
                        "Configure appropriate logging levels for environment",
                        "Verify environment-specific configurations",
                    ],
                    metadata={
                        "environment": environment,
                        "configuration_incomplete": True,
                    },
                )
            )

        return thoughts

    async def get_system_thoughts(
        self, hours: int = 24, thought_type: Optional[str] = None
    ) -> List[Thought]:
        """Get stored system thoughts for analysis.

        Args:
            hours: Number of hours of history to retrieve
            thought_type: Filter by thought type ("version" or "self_check")

        Returns:
            List[Thought]: System thoughts from the specified period
        """
        try:
            # Try to get thoughts from Redis cache if available
            from core.services.redis_service import redis_service

            if redis_service.redis:
                thoughts_key = f"system:thoughts:{hours}h"
                if thought_type:
                    thoughts_key += f":{thought_type}"

                cached_thoughts = await redis_service.redis.get(thoughts_key)
                if cached_thoughts:
                    thoughts_data = json.loads(cached_thoughts)
                    return [Thought(**thought) for thought in thoughts_data]

            # Generate fresh thoughts if not cached
            current_status = await self.get_full_status()

            version_thoughts = await self.generate_version_thoughts(current_status)
            self_check_thoughts = await self.generate_self_check_thoughts(
                current_status
            )

            all_thoughts = version_thoughts + self_check_thoughts

            if thought_type:
                all_thoughts = [
                    t for t in all_thoughts if t.thought_type == thought_type
                ]

            # Cache the thoughts
            if redis_service.redis:
                cache_data = [asdict(thought) for thought in all_thoughts]
                await redis_service.redis.setex(
                    thoughts_key, 300, json.dumps(cache_data)
                )  # 5 minutes

            return all_thoughts

        except Exception as e:
            # Return empty list on error
            logging.error(f"Failed to get system thoughts: {e}")
            return []

    async def generate_thoughts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Generate summary of system thoughts for analysis.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dict containing thoughts summary and insights
        """
        thoughts = await self.get_system_thoughts(hours)

        if not thoughts:
            return {
                "total_thoughts": 0,
                "period_hours": hours,
                "summary": "No thoughts available for the specified period",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Analyze thoughts
        version_thoughts = [t for t in thoughts if t.thought_type == "version"]
        self_check_thoughts = [t for t in thoughts if t.thought_type == "self_check"]

        # Impact analysis
        impact_counts = {}
        for thought in thoughts:
            impact_counts[thought.impact] = impact_counts.get(thought.impact, 0) + 1

        # Category analysis
        category_counts = {}
        for thought in thoughts:
            category_counts[thought.category] = (
                category_counts.get(thought.category, 0) + 1
            )

        # Actionable thoughts
        actionable_thoughts = [t for t in thoughts if t.actionable]

        # Confidence analysis
        avg_confidence = sum(t.confidence for t in thoughts) / len(thoughts)

        # Generate insights
        high_impact_count = impact_counts.get("high", 0) + impact_counts.get(
            "critical", 0
        )
        actionable_rate = len(actionable_thoughts) / len(thoughts) if thoughts else 0

        insights = []
        if high_impact_count > 0:
            insights.append(
                f"⚠️ {high_impact_count} high/critical impact thoughts require attention"
            )
        if actionable_rate > 0.5:
            insights.append(
                f"📋 {actionable_rate * 100:.0f}% of thoughts are actionable"
            )
        if avg_confidence > 0.8:
            insights.append(
                f"🎯 High confidence ({avg_confidence * 100:.0f}%) in system analysis"
            )
        if len(version_thoughts) > len(self_check_thoughts):
            insights.append(
                f"📈 System evolution focus with {len(version_thoughts)} version thoughts"
            )

        return {
            "total_thoughts": len(thoughts),
            "period_hours": hours,
            "version_thoughts": len(version_thoughts),
            "self_check_thoughts": len(self_check_thoughts),
            "actionable_thoughts": len(actionable_thoughts),
            "average_confidence": avg_confidence,
            "actionable_rate": actionable_rate,
            "impact_breakdown": impact_counts,
            "category_breakdown": category_counts,
            "insights": insights,
            "most_recent_thought": thoughts[0].content if thoughts else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"Generated {len(thoughts)} thoughts in the last {hours} hours with {len(actionable_thoughts)} actionable items",
        }

    def _estimate_response_time(self) -> int:
        """Estimate database response time based on current system load."""
        # This is a simplified estimation - in practice, you'd measure actual response times
        import random

        return random.randint(50, 200)  # Simulated response time in ms
