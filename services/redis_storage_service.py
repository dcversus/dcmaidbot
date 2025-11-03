"""
Redis Storage Service for Operational Data

Optimized Redis-based storage for all thoughts, crypto data, and operational
information needed for /status endpoint and tools with proper invalidation mechanisms.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.redis_service import RedisService

logger = logging.getLogger(__name__)


class RedisStorageService:
    """
    Redis-based storage service for all operational data.

    Features:
    - Structured key naming for easy management
    - TTL-based expiration for automatic cleanup
    - Atomic operations for consistency
    - Cache invalidation strategies
    - Health monitoring and metrics
    """

    def __init__(self, redis_service: RedisService):
        """Initialize Redis storage service."""
        self.redis_service_service = redis_service

        # Key prefixes for organized storage
        self.prefixes = {
            "thoughts": "dc:thoughts:",
            "version": "dc:version:",
            "self_check": "dc:self_check:",
            "crypto": "dc:crypto:",
            "crypto_data": "dc:crypto_data:",
            "admin_interactions": "dc:admin_interactions:",
            "llm_context": "dc:llm_context:",
            "tokens": "dc:tokens:",
            "metrics": "dc:metrics:",
            "locks": "dc:locks:",
        }

        # TTL configuration (in seconds)
        self.ttls = {
            "thoughts_version": 86400 * 30,  # 30 days
            "thoughts_self_check": 86400 * 7,  # 7 days
            "thoughts_crypto": 86400 * 3,  # 3 days
            "crypto_data": 86400 * 7,  # 7 days
            "admin_interactions": 86400 * 30,  # 30 days
            "llm_context": 3600,  # 1 hour
            "tokens": 86400 * 7,  # 7 days
            "metrics": 3600,  # 1 hour
            "locks": 300,  # 5 minutes
        }

        # Maximum list sizes
        self.max_list_sizes = {
            "crypto_data": 20,  # Keep last 20 crypto data records
            "admin_interactions": 1000,  # Keep last 1000 interactions
            "llm_context": 100,  # Keep last 100 context items
        }

    async def store_version_thoughts(
        self,
        version: str,
        thoughts_data: Dict[str, Any],
        previous_version: Optional[str] = None,
    ) -> bool:
        """Store version thoughts in Redis with proper TTL."""
        try:
            key = f"{self.prefixes['thoughts']}version:{version}"

            # Store with version metadata
            storage_data = {
                **thoughts_data,
                "version": version,
                "previous_version": previous_version,
                "stored_at": datetime.now(timezone.utc).isoformat(),
            }

            # Store in Redis with TTL
            success = await self.redis_service_service.setex(
                key, self.ttls["thoughts_version"], json.dumps(storage_data)
            )

            if success:
                # Update latest version reference
                await self.redis_service_service.setex(
                    f"{self.prefixes['version']}latest",
                    self.ttls["thoughts_version"],
                    json.dumps(
                        {"version": version, "timestamp": storage_data["stored_at"]}
                    ),
                )

                # Invalidate version cache
                await self.invalidate_cache_pattern("version:*")

            logger.info(f"Stored version thoughts for {version}")
            return success

        except Exception as e:
            logger.error(f"Failed to store version thoughts: {e}")
            return False

    async def get_version_thoughts(
        self, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get version thoughts from Redis."""
        try:
            if version:
                # Get specific version
                key = f"{self.prefixes['thoughts']}version:{version}"
                data = await self.redis_service_service.get(key)
                return json.loads(data) if data else {}
            else:
                # Get latest version
                latest_key = f"{self.prefixes['version']}latest"
                latest_data = await self.redis_service_service.get(latest_key)

                if latest_data:
                    latest_info = json.loads(latest_data)
                    return await self.get_version_thoughts(latest_info["version"])

                return {}

        except Exception as e:
            logger.error(f"Failed to get version thoughts: {e}")
            return {}

    async def store_self_check_thoughts(self, thoughts_data: Dict[str, Any]) -> bool:
        """Store self-check thoughts with TTL."""
        try:
            # Store latest self-check thoughts
            latest_key = f"{self.prefixes['thoughts']}self_check:latest"
            success = await self.redis_service_service.setex(
                latest_key, self.ttls["thoughts_self_check"], json.dumps(thoughts_data)
            )

            if success:
                # Store in history (keep last 7 days with timestamp keys)
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                history_key = f"{self.prefixes['thoughts']}self_check:{timestamp}"
                await self.redis_service_service.setex(
                    history_key,
                    self.ttls["thoughts_self_check"],
                    json.dumps(thoughts_data),
                )

                # Invalidate self-check cache
                await self.invalidate_cache_pattern("self_check:*")

            logger.info("Stored self-check thoughts")
            return success

        except Exception as e:
            logger.error(f"Failed to store self-check thoughts: {e}")
            return False

    async def get_self_check_thoughts(self) -> Dict[str, Any]:
        """Get latest self-check thoughts from Redis."""
        try:
            key = f"{self.prefixes['thoughts']}self_check:latest"
            data = await self.redis_service_service.get(key)
            return json.loads(data) if data else {}

        except Exception as e:
            logger.error(f"Failed to get self-check thoughts: {e}")
            return {}

    async def store_crypto_thoughts(self, thoughts_data: Dict[str, Any]) -> bool:
        """Store crypto thoughts with TTL."""
        try:
            # Store latest crypto thoughts
            latest_key = f"{self.prefixes['thoughts']}crypto:latest"
            success = await self.redis_service_service.setex(
                latest_key, self.ttls["thoughts_crypto"], json.dumps(thoughts_data)
            )

            if success:
                # Store in history
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                history_key = f"{self.prefixes['thoughts']}crypto:{timestamp}"
                await self.redis_service_service.setex(
                    history_key, self.ttls["thoughts_crypto"], json.dumps(thoughts_data)
                )

                # Invalidate crypto cache
                await self.invalidate_cache_pattern("crypto:*")

            logger.info("Stored crypto thoughts")
            return success

        except Exception as e:
            logger.error(f"Failed to store crypto thoughts: {e}")
            return False

    async def get_crypto_thoughts(self) -> Dict[str, Any]:
        """Get latest crypto thoughts from Redis."""
        try:
            key = f"{self.prefixes['thoughts']}crypto:latest"
            data = await self.redis_service_service.get(key)
            return json.loads(data) if data else {}

        except Exception as e:
            logger.error(f"Failed to get crypto thoughts: {e}")
            return {}

    async def store_crypto_data(self, crypto_data: Dict[str, Any]) -> bool:
        """Store raw crypto API data in Redis list."""
        try:
            # Use Redis list to maintain history
            list_key = f"{self.prefixes['crypto_data']}history"

            # Add to list (left push for newest first)
            data_json = json.dumps(
                {**crypto_data, "stored_at": datetime.now(timezone.utc).isoformat()}
            )

            await self.redis_service.lpush(list_key, data_json)

            # Trim list to max size
            await self.redis_service.ltrim(
                list_key, 0, self.max_list_sizes["crypto_data"] - 1
            )

            # Set TTL on the list
            await self.redis_service.expire(list_key, self.ttls["crypto_data"])

            # Update latest crypto data reference
            latest_key = f"{self.prefixes['crypto_data']}latest"
            await self.redis_service_service.setex(
                latest_key, self.ttls["crypto_data"], data_json
            )

            logger.info(
                f"Stored crypto data (list size: {await self.redis_service.llen(list_key)})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store crypto data: {e}")
            return False

    async def get_crypto_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get crypto data history from Redis."""
        try:
            list_key = f"{self.prefixes['crypto_data']}history"

            # Get range from list (0 to limit-1 for newest records)
            raw_data = await self.redis_service.lrange(list_key, 0, limit - 1)

            crypto_data = []
            for item in raw_data:
                try:
                    crypto_data.append(json.loads(item))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode crypto data: {item[:50]}...")

            return crypto_data

        except Exception as e:
            logger.error(f"Failed to get crypto data: {e}")
            return []

    async def store_admin_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Store admin interaction in Redis list."""
        try:
            list_key = f"{self.prefixes['admin_interactions']}history"

            # Add interaction data
            data_json = json.dumps(
                {
                    **interaction_data,
                    "stored_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            await self.redis_service.lpush(list_key, data_json)

            # Trim list to max size
            await self.redis_service.ltrim(
                list_key, 0, self.max_list_sizes["admin_interactions"] - 1
            )

            # Set TTL
            await self.redis_service.expire(list_key, self.ttls["admin_interactions"])

            logger.debug(
                f"Stored admin interaction (list size: {await self.redis_service.llen(list_key)})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store admin interaction: {e}")
            return False

    async def get_admin_interactions(
        self,
        page: int = 1,
        per_page: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get paginated admin interactions from Redis."""
        try:
            list_key = f"{self.prefixes['admin_interactions']}history"

            # Get total count
            total = await self.redis_service.llen(list_key)

            # Calculate pagination
            start = (page - 1) * per_page
            end = start + per_page - 1

            # Get paginated data
            raw_data = await self.redis_service.lrange(list_key, start, end)

            interactions = []
            for item in raw_data:
                try:
                    interaction = json.loads(item)

                    # Apply filters if provided
                    if filters:
                        if filters.get("user_id") and str(
                            interaction.get("user_id")
                        ) != str(filters["user_id"]):
                            continue
                        if (
                            filters.get("interaction_type")
                            and interaction.get("interaction_type")
                            != filters["interaction_type"]
                        ):
                            continue
                        if filters.get("date_from"):
                            # Simple date filter (could be enhanced)
                            try:
                                interaction_date = datetime.fromisoformat(
                                    interaction.get("timestamp", "").replace(
                                        "Z", "+00:00"
                                    )
                                )
                                date_from = datetime.fromisoformat(
                                    filters["date_from"].replace("Z", "+00:00")
                                )
                                if interaction_date < date_from:
                                    continue
                            except (ValueError, TypeError, AttributeError):
                                continue

                    interactions.append(interaction)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode interaction: {item[:50]}...")

            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page

            return {
                "interactions": interactions,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                },
                "filters": filters or {},
            }

        except Exception as e:
            logger.error(f"Failed to get admin interactions: {e}")
            return {
                "interactions": [],
                "pagination": {"error": str(e)},
                "filters": filters or {},
            }

    async def store_llm_context(self, context_data: Dict[str, Any]) -> bool:
        """Store LLM context in Redis list."""
        try:
            list_key = f"{self.prefixes['llm_context']}history"

            # Add context data
            data_json = json.dumps(
                {**context_data, "stored_at": datetime.now(timezone.utc).isoformat()}
            )

            await self.redis_service.lpush(list_key, data_json)

            # Trim list to max size
            await self.redis_service.ltrim(
                list_key, 0, self.max_list_sizes["llm_context"] - 1
            )

            # Set TTL
            await self.redis_service.expire(list_key, self.ttls["llm_context"])

            # Store current context
            current_key = f"{self.prefixes['llm_context']}current"
            await self.redis_service_service.setex(
                current_key, self.ttls["llm_context"], data_json
            )

            logger.debug(
                f"Stored LLM context (list size: {await self.redis_service.llen(list_key)})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store LLM context: {e}")
            return False

    async def get_llm_context(self) -> Dict[str, Any]:
        """Get current LLM context from Redis."""
        try:
            current_key = f"{self.prefixes['llm_context']}current"
            data = await self.redis_service_service.get(current_key)
            return (
                json.loads(data)
                if data
                else {
                    "current_context": "No active context",
                    "recent_prompts": [],
                    "token_usage_today": 0,
                    "last_llm_interaction": None,
                    "context_size": 0,
                    "active_sessions": 0,
                }
            )

        except Exception as e:
            logger.error(f"Failed to get LLM context: {e}")
            return {"error": str(e)}

    async def track_token_usage(
        self, tokens_used: int, source: str = "unknown"
    ) -> bool:
        """Track token usage in Redis."""
        try:
            # Store daily usage
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            daily_key = f"{self.prefixes['tokens']}daily:{today}"

            # Increment daily counter
            await self.redis_service.incrby(daily_key, tokens_used)
            await self.redis_service.expire(daily_key, self.ttls["tokens"])

            # Store total usage
            total_key = f"{self.prefixes['tokens']}total"
            await self.redis_service.incrby(total_key, tokens_used)

            # Store usage with timestamp
            usage_key = f"{self.prefixes['tokens']}usage:{datetime.now(timezone.utc).isoformat()}"
            await self.redis_service_service.setex(
                usage_key,
                self.ttls["tokens"],
                json.dumps(
                    {
                        "tokens": tokens_used,
                        "source": source,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
            )

            logger.debug(f"Tracked {tokens_used} tokens from {source}")
            return True

        except Exception as e:
            logger.error(f"Failed to track token usage: {e}")
            return False

    async def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage statistics from Redis."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            daily_key = f"{self.prefixes['tokens']}daily:{today}"
            total_key = f"{self.prefixes['tokens']}total"

            daily_usage = await self.redis_service_service.get(daily_key) or "0"
            total_usage = await self.redis_service_service.get(total_key) or "0"

            return {
                "daily_usage": int(daily_usage),
                "total_usage": int(total_usage),
                "date": today,
            }

        except Exception as e:
            logger.error(f"Failed to get token usage: {e}")
            return {"error": str(e)}

    async def acquire_lock(self, lock_name: str, timeout: int = 300) -> bool:
        """Acquire a distributed lock."""
        try:
            lock_key = f"{self.prefixes['locks']}{lock_name}"

            # Try to set lock with expiration
            success = await self.redis_service_service.set(
                lock_key, "locked", ex=timeout, nx=True
            )

            if success:
                logger.debug(f"Acquired lock: {lock_name}")
            else:
                logger.debug(f"Failed to acquire lock: {lock_name}")

            return success

        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_name}: {e}")
            return False

    async def release_lock(self, lock_name: str) -> bool:
        """Release a distributed lock."""
        try:
            lock_key = f"{self.prefixes['locks']}{lock_name}"
            result = await self.redis_service_service.delete(lock_key)

            if result:
                logger.debug(f"Released lock: {lock_name}")

            return result

        except Exception as e:
            logger.error(f"Failed to release lock {lock_name}: {e}")
            return False

    async def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern."""
        try:
            # Find keys matching pattern
            keys = []
            cursor = 0

            while True:
                cursor, found_keys = await self.redis_service.scan(
                    cursor, match=pattern, count=100
                )
                keys.extend(found_keys)

                if cursor == 0:
                    break

            # Delete found keys
            deleted = 0
            if keys:
                deleted = await self.redis_service_service.delete(*keys)

            logger.info(f"Invalidated {deleted} cache keys matching pattern: {pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
            return 0

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage metrics and health status."""
        try:
            metrics = {
                "redis_connected": await self.redis_service.ping(),
                "storage_keys": {},
                "memory_usage": {},
                "cache_health": {},
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            if not metrics["redis_connected"]:
                return metrics

            # Count keys by prefix
            for prefix_name, prefix in self.prefixes.items():
                if prefix_name not in ["locks"]:  # Skip lock keys
                    pattern = f"{prefix}*"
                    cursor = 0
                    count = 0

                    while True:
                        cursor, keys = await self.redis_service.scan(
                            cursor, match=pattern, count=1000
                        )
                        count += len(keys)
                        if cursor == 0:
                            break

                    metrics["storage_keys"][prefix_name] = count

            # Get memory usage info
            try:
                info = await self.redis_service.info("memory")
                metrics["memory_usage"] = {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "used_memory_peak": info.get("used_memory_peak", 0),
                    "used_memory_peak_human": info.get(
                        "used_memory_peak_human", "unknown"
                    ),
                }
            except Exception as e:
                logger.error(f"Failed to get memory info: {e}")

            return metrics

        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return {
                "redis_connected": False,
                "error": str(e),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data and return cleanup statistics."""
        try:
            cleanup_stats = {
                "keys_deleted": 0,
                "patterns_checked": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Check for expired keys (TTL should handle this automatically, but we can be explicit)
            for prefix_name, prefix in self.prefixes.items():
                if prefix_name in [
                    "thoughts",
                    "version",
                    "crypto_data",
                ]:  # Check important prefixes
                    pattern = f"{prefix}*"
                    cursor = 0
                    keys_to_check = []

                    while True:
                        cursor, keys = await self.redis_service.scan(
                            cursor, match=pattern, count=100
                        )
                        keys_to_check.extend(keys)
                        if cursor == 0:
                            break

                    for key in keys_to_check:
                        try:
                            ttl = await self.redis_service.ttl(key)
                            if ttl == -1:  # No expiration set
                                # Set appropriate TTL for keys without expiration
                                if "thoughts:" in key:
                                    await self.redis_service.expire(
                                        key, self.ttls.get("thoughts_version", 86400)
                                    )
                                elif "crypto_data:" in key:
                                    await self.redis_service.expire(
                                        key, self.ttls.get("crypto_data", 604800)
                                    )
                            elif (
                                ttl == -2
                            ):  # Key doesn't exist (shouldn't happen with scan)
                                pass
                        except Exception:
                            continue

                    cleanup_stats["patterns_checked"].append(prefix_name)

            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return {
                "keys_deleted": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
