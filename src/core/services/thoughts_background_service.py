"""
Background Tasks Service for Thoughts Generation

Handles asynchronous generation of version thoughts, self-check thoughts,
and crypto thoughts with timing data storage and scheduled execution.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from src.core.services.llm_service import LLMService
from src.core.services.redis_service import RedisService
from src.core.services.redis_storage_service import RedisStorageService
from src.core.services.status_enhanced_service import EnhancedStatusService

logger = logging.getLogger(__name__)


class ThoughtsBackgroundService:
    """
    Background service for managing thoughts generation with timing data storage.

    This service handles:
    - Version thoughts generation on version changes
    - Self-check thoughts generation on startup and scheduled intervals
    - Crypto thoughts generation on schedule (twice daily)
    - Timing data storage and retrieval
    - Background task management
    """

    def __init__(self):
        """Initialize the background thoughts service with Redis storage."""
        self.llm_service = LLMService()
        self.enhanced_status_service = EnhancedStatusService(self.llm_service)

        # Initialize Redis services
        redis_service = RedisService()
        self.redis_storage = RedisStorageService(redis_service)

        # Track last execution times (in-memory for quick access)
        self.last_version_thoughts = None
        self.last_self_check_thoughts = None
        self.last_crypto_thoughts = None

        # Background tasks
        self.version_task = None
        self.self_check_task = None
        self.crypto_task = None

        # Configuration
        self.self_check_interval = timedelta(hours=24)  # Every 24 hours
        self.crypto_thoughts_interval = timedelta(hours=12)  # Twice daily

        # Lock names for distributed operations
        self.locks = {
            "version_thoughts": "version_thoughts_generation",
            "self_check_thoughts": "self_check_generation",
            "crypto_thoughts": "crypto_thoughts_generation",
        }

    async def start_background_tasks(self) -> None:
        """Start all background tasks for thoughts generation."""
        logger.info("Starting background thoughts generation tasks...")

        # Start self-check task
        if not self.self_check_task or self.self_check_task.done():
            self.self_check_task = asyncio.create_task(self._self_check_scheduler())
            logger.info("Self-check thoughts scheduler started")

        # Start crypto thoughts task
        if not self.crypto_task or self.crypto_task.done():
            self.crypto_task = asyncio.create_task(self._crypto_thoughts_scheduler())
            logger.info("Crypto thoughts scheduler started")

        # Generate initial self-check thoughts
        asyncio.create_task(self._generate_self_check_thoughts_now())

        # Generate initial crypto thoughts
        asyncio.create_task(self._generate_crypto_thoughts_now())

    async def stop_background_tasks(self) -> None:
        """Stop all background tasks."""
        logger.info("Stopping background thoughts generation tasks...")

        if self.self_check_task and not self.self_check_task.done():
            self.self_check_task.cancel()
            try:
                await self.self_check_task
            except asyncio.CancelledError:
                pass

        if self.crypto_task and not self.crypto_task.done():
            self.crypto_task.cancel()
            try:
                await self.crypto_task
            except asyncio.CancelledError:
                pass

        logger.info("Background thoughts generation tasks stopped")

    async def trigger_version_thoughts(
        self, changelog_content: str, version: str
    ) -> Dict[str, Any]:
        """
        Trigger version thoughts generation when version changes.

        Args:
            changelog_content: The changelog content for version thoughts
            version: The new version string

        Returns:
            Dict: Generated version thoughts with timing data
        """
        logger.info(f"Triggering version thoughts for version: {version}")

        # Acquire distributed lock
        lock_acquired = await self.redis_storage.acquire_lock(
            self.locks["version_thoughts"], timeout=300
        )

        if not lock_acquired:
            logger.warning("Version thoughts generation already in progress")
            return {
                "available": False,
                "content": "Version thoughts generation already in progress",
                "technical_summary": "Process running",
                "lilith_opinion": "I'm already thinking about the version... Please wait a moment!",
                "generation_time": 0,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": "Lock acquisition failed",
            }

        try:
            start_time = time.time()

            # Get previous version thoughts from Redis for context
            previous_version_thoughts = await self.redis_storage.get_version_thoughts()
            previous_thoughts = (
                previous_version_thoughts.get("lilith_opinion")
                if previous_version_thoughts
                else None
            )

            # Generate version thoughts
            version_result = (
                await self.enhanced_status_service.generate_version_thoughts(
                    changelog_content=changelog_content,
                    previous_version_thoughts=previous_thoughts,
                )
            )

            generation_time = time.time() - start_time

            # Store with timing data in Redis
            stored_thoughts = {
                "available": version_result.get("success", False),
                "content": version_result.get("version_thoughts", ""),
                "technical_summary": version_result.get("technical_summary", ""),
                "lilith_opinion": version_result.get("lilith_opinion", ""),
                "generation_time": generation_time,
                "tokens_used": version_result.get("tokens_used", 0),
                "last_updated": version_result.get("timestamp"),
                "success": version_result.get("success", False),
                "version": version,
                "changelog_content": changelog_content,
            }

            # Get previous version for comparison
            latest_version_info = await self.redis_storage.get_version_thoughts()
            previous_version = (
                latest_version_info.get("version") if latest_version_info else None
            )

            # Store in Redis
            redis_success = await self.redis_storage.store_version_thoughts(
                version=version,
                thoughts_data=stored_thoughts,
                previous_version=previous_version,
            )

            if redis_success:
                self.last_version_thoughts = stored_thoughts

                # Track token usage
                await self.redis_storage.track_token_usage(
                    stored_thoughts["tokens_used"], f"version_thoughts:{version}"
                )

                logger.info(
                    f"Version thoughts generated and stored in {generation_time:.2f}s"
                )
            else:
                logger.error("Failed to store version thoughts in Redis")

            return stored_thoughts

        except Exception as e:
            logger.error(f"Failed to generate version thoughts: {e}")

            error_thoughts = {
                "available": False,
                "content": f"Error generating version thoughts: {str(e)}",
                "technical_summary": "Error occurred",
                "lilith_opinion": f"I'm confused about this version update... Something went wrong! Error: {str(e)}",
                "generation_time": time.time() - start_time,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "version": version,
                "error": str(e),
            }

            return error_thoughts

        finally:
            # Always release the lock
            await self.redis_storage.release_lock(self.locks["version_thoughts"])

    async def _self_check_scheduler(self) -> None:
        """Background scheduler for self-check thoughts generation."""
        logger.info("Self-check thoughts scheduler started")

        while True:
            try:
                await asyncio.sleep(self.self_check_interval.total_seconds())
                await self._generate_self_check_thoughts_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Self-check scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _crypto_thoughts_scheduler(self) -> None:
        """Background scheduler for crypto thoughts generation (twice daily)."""
        logger.info("Crypto thoughts scheduler started (runs twice daily)")

        # Calculate next run times (every 12 hours)
        while True:
            try:
                # Sleep for 12 hours
                await asyncio.sleep(self.crypto_thoughts_interval.total_seconds())
                await self._generate_crypto_thoughts_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Crypto thoughts scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    async def _generate_self_check_thoughts_now(self) -> Dict[str, Any]:
        """Generate self-check thoughts immediately with Redis storage."""
        logger.info("Generating self-check thoughts...")

        # Acquire distributed lock
        lock_acquired = await self.redis_storage.acquire_lock(
            self.locks["self_check_thoughts"], timeout=300
        )

        if not lock_acquired:
            logger.warning("Self-check thoughts generation already in progress")
            return {
                "available": False,
                "content": "Self-check generation already in progress",
                "technical_report": "Process running",
                "lilith_honest_opinion": "I'm already checking my systems... Please wait a moment!",
                "tool_results": [],
                "total_time": 0,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": "Lock acquisition failed",
            }

        try:
            start_time = time.time()

            # Generate self-check thoughts
            self_check_result = (
                await self.enhanced_status_service.generate_self_check_thoughts()
            )

            generation_time = time.time() - start_time

            # Store with timing data
            stored_thoughts = {
                "available": self_check_result.get("success", False),
                "content": self_check_result.get("self_check_thoughts", ""),
                "technical_report": self_check_result.get("technical_report", ""),
                "lilith_honest_opinion": self_check_result.get(
                    "lilith_honest_opinion", ""
                ),
                "tool_results": self_check_result.get("tool_results", []),
                "total_time": generation_time,
                "tokens_used": self_check_result.get("tokens_used", 0),
                "last_updated": self_check_result.get("timestamp"),
                "success": self_check_result.get("success", False),
            }

            # Store in Redis
            redis_success = await self.redis_storage.store_self_check_thoughts(
                stored_thoughts
            )

            if redis_success:
                self.last_self_check_thoughts = stored_thoughts

                # Track token usage
                await self.redis_storage.track_token_usage(
                    stored_thoughts["tokens_used"], "self_check_thoughts"
                )

                logger.info(
                    f"Self-check thoughts generated and stored in {generation_time:.2f}s"
                )
            else:
                logger.error("Failed to store self-check thoughts in Redis")

            return stored_thoughts

        except Exception as e:
            logger.error(f"Failed to generate self-check thoughts: {e}")

            error_thoughts = {
                "available": False,
                "content": f"Self-check failed: {str(e)}",
                "technical_report": "Error occurred during self-check",
                "lilith_honest_opinion": f"I'm feeling overwhelmed by all these errors... Something's not right with my systems! Error: {str(e)}",
                "tool_results": [],
                "total_time": time.time() - start_time,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": str(e),
            }

            return error_thoughts

        finally:
            # Always release the lock
            await self.redis_storage.release_lock(self.locks["self_check_thoughts"])

    async def _generate_crypto_thoughts_now(self) -> Dict[str, Any]:
        """Generate crypto thoughts immediately with Redis storage."""
        logger.info("Generating crypto thoughts...")

        # Acquire distributed lock
        lock_acquired = await self.redis_storage.acquire_lock(
            self.locks["crypto_thoughts"], timeout=600
        )  # Longer timeout for API calls

        if not lock_acquired:
            logger.warning("Crypto thoughts generation already in progress")
            return {
                "available": False,
                "content": "Crypto thoughts generation already in progress",
                "market_analysis": "Process running",
                "irrational_behavior": "I'm already analyzing the crypto markets... Please wait!",
                "uncomfortable_truth": "Even crypto therapists need a moment to think!",
                "generation_time": 0,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": "Lock acquisition failed",
            }

        try:
            start_time = time.time()

            # Generate crypto thoughts
            crypto_result = await self.enhanced_status_service.crypto_service.generate_crypto_thoughts(
                force_refresh=True
            )

            generation_time = time.time() - start_time

            # Store raw API results in Redis
            crypto_data_record = {
                "timestamp": crypto_result.timestamp,
                "market_data": crypto_result.market_data_summary,
                "news_summary": crypto_result.news_summary,
                "confidence_score": crypto_result.confidence_score,
                "therapeutic_tone": crypto_result.therapeutic_tone,
                "processing_time_seconds": crypto_result.processing_time_seconds,
                "tokens_used": crypto_result.tokens_used,
            }

            # Store crypto data in Redis list
            await self.redis_storage.store_crypto_data(crypto_data_record)

            # Store thoughts with timing data
            stored_thoughts = {
                "available": True,  # Crypto thoughts always generate something
                "content": f"{crypto_result.market_analysis}\n\n{crypto_result.irrational_behavior}\n\n{crypto_result.uncomfortable_truth}",
                "market_analysis": crypto_result.market_analysis,
                "irrational_behavior": crypto_result.irrational_behavior,
                "uncomfortable_truth": crypto_result.uncomfortable_truth,
                "generation_time": generation_time,
                "tokens_used": crypto_result.tokens_used,
                "last_updated": crypto_result.timestamp,
                "success": True,
                "confidence_score": crypto_result.confidence_score,
                "therapeutic_tone": crypto_result.therapeutic_tone,
                "market_data_summary": crypto_result.market_data_summary,
                "news_summary": crypto_result.news_summary,
                "api_results": crypto_data_record,  # Include raw API results
            }

            # Store crypto thoughts in Redis
            redis_success = await self.redis_storage.store_crypto_thoughts(
                stored_thoughts
            )

            if redis_success:
                self.last_crypto_thoughts = stored_thoughts

                # Track token usage
                await self.redis_storage.track_token_usage(
                    stored_thoughts["tokens_used"], "crypto_thoughts"
                )

                logger.info(
                    f"Crypto thoughts generated and stored in {generation_time:.2f}s"
                )
            else:
                logger.error("Failed to store crypto thoughts in Redis")

            return stored_thoughts

        except Exception as e:
            logger.error(f"Failed to generate crypto thoughts: {e}")

            error_thoughts = {
                "available": False,
                "content": f"Crypto thoughts failed: {str(e)}",
                "market_analysis": "Market analysis unavailable",
                "irrational_behavior": "Cannot analyze behavior right now",
                "uncomfortable_truth": "Even crypto therapists have technical difficulties sometimes...",
                "generation_time": time.time() - start_time,
                "tokens_used": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "error": str(e),
            }

            return error_thoughts

        finally:
            # Always release the lock
            await self.redis_storage.release_lock(self.locks["crypto_thoughts"])

    async def get_stored_crypto_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get stored crypto API results from Redis.

        Args:
            limit: Maximum number of records to return

        Returns:
            List[Dict]: Stored crypto data records
        """
        try:
            # Get from Redis storage
            return await self.redis_storage.get_crypto_data(limit)
        except Exception as e:
            logger.error(f"Failed to get stored crypto data: {e}")
            return []

    async def get_stored_thoughts(self) -> Dict[str, Any]:
        """
        Get all stored thoughts with timing data from Redis.

        Returns:
            Dict: All stored thoughts data
        """
        try:
            # Get all thoughts from Redis
            version_thoughts = await self.redis_storage.get_version_thoughts()
            self_check_thoughts = await self.redis_storage.get_self_check_thoughts()
            crypto_thoughts = await self.redis_storage.get_crypto_thoughts()

            # Update in-memory cache for quick access
            self.last_version_thoughts = version_thoughts
            self.last_self_check_thoughts = self_check_thoughts
            self.last_crypto_thoughts = crypto_thoughts

            return {
                "version_thoughts": version_thoughts,
                "self_check_thoughts": self_check_thoughts,
                "crypto_thoughts": crypto_thoughts,
            }

        except Exception as e:
            logger.error(f"Failed to get stored thoughts from Redis: {e}")
            return {
                "version_thoughts": self.last_version_thoughts or {},
                "self_check_thoughts": self.last_self_check_thoughts or {},
                "crypto_thoughts": self.last_crypto_thoughts or {},
            }

    async def get_thought_summary(self) -> Dict[str, Any]:
        """
        Get summary of thoughts status and timing with Redis health monitoring.

        Returns:
            Dict: Summary of all thoughts status with Redis health metrics
        """
        now = datetime.now(timezone.utc)

        # Check Redis health
        redis_health = await self._get_redis_health()

        summary = {
            "timestamp": now.isoformat(),
            "version_thoughts_status": {
                "available": bool(self.last_version_thoughts),
                "last_updated": self.last_version_thoughts.get("last_updated")
                if self.last_version_thoughts
                else None,
                "generation_time": self.last_version_thoughts.get("generation_time")
                if self.last_version_thoughts
                else None,
                "tokens_used": self.last_version_thoughts.get("tokens_used", 0)
                if self.last_version_thoughts
                else 0,
            },
            "self_check_thoughts_status": {
                "available": bool(self.last_self_check_thoughts),
                "last_updated": self.last_self_check_thoughts.get("last_updated")
                if self.last_self_check_thoughts
                else None,
                "total_time": self.last_self_check_thoughts.get("total_time")
                if self.last_self_check_thoughts
                else None,
                "tokens_used": self.last_self_check_thoughts.get("tokens_used", 0)
                if self.last_self_check_thoughts
                else 0,
            },
            "crypto_thoughts_status": {
                "available": bool(self.last_crypto_thoughts),
                "last_updated": self.last_crypto_thoughts.get("last_updated")
                if self.last_crypto_thoughts
                else None,
                "generation_time": self.last_crypto_thoughts.get("generation_time")
                if self.last_crypto_thoughts
                else None,
                "tokens_used": self.last_crypto_thoughts.get("tokens_used", 0)
                if self.last_crypto_thoughts
                else 0,
            },
            "background_tasks_status": {
                "self_check_scheduler_active": self.self_check_task
                and not self.self_check_task.done(),
                "crypto_scheduler_active": self.crypto_task
                and not self.crypto_task.done(),
            },
            "redis_storage_status": redis_health,
        }

        return summary

    async def _get_redis_health(self) -> Dict[str, Any]:
        """
        Check Redis storage health and gather metrics.

        Returns:
            Dict: Redis health status and metrics
        """
        try:
            start_time = time.time()

            # Test Redis connection with a simple operation
            test_key = f"{self.redis_storage.prefixes['metrics']}health_check"
            test_value = str(time.time())

            # Test write
            write_success = await self.redis_storage.redis_service.set(
                test_key, test_value, expire=30
            )
            write_time = time.time() - start_time

            # Test read
            read_start = time.time()
            read_value = await self.redis_storage.redis_service.get(test_key)
            read_time = time.time() - read_start

            # Cleanup
            await self.redis_storage.redis_service.delete(test_key)

            # Get storage metrics
            total_time = time.time() - start_time
            is_connected = write_success and read_value == test_value

            # Get Redis info if available
            redis_info = {}
            if (
                is_connected
                and hasattr(self.redis_storage.redis_service, "redis")
                and self.redis_storage.redis_service.redis
            ):
                try:
                    info = await self.redis_storage.redis_service.redis.info()
                    redis_info = {
                        "used_memory": info.get("used_memory_human"),
                        "connected_clients": info.get("connected_clients"),
                        "total_commands_processed": info.get(
                            "total_commands_processed"
                        ),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                    }
                except Exception:
                    pass  # Redis info not available

            return {
                "connected": is_connected,
                "response_time_ms": round(total_time * 1000, 2),
                "write_time_ms": round(write_time * 1000, 2),
                "read_time_ms": round(read_time * 1000, 2),
                "last_health_check": datetime.now(timezone.utc).isoformat(),
                "storage_keys_prefixes": list(self.redis_storage.prefixes.values()),
                "ttl_configuration": self.redis_storage.ttls,
                "redis_info": redis_info,
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "last_health_check": datetime.now(timezone.utc).isoformat(),
                "storage_keys_prefixes": list(self.redis_storage.prefixes.values()),
                "ttl_configuration": self.redis_storage.ttls,
            }


# Global instance for the service
thoughts_background_service = ThoughtsBackgroundService()
