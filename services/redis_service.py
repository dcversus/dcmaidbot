"""Redis connection service for caching."""

import json
import os
from typing import Any, Optional

import redis.asyncio as aioredis  # type: ignore[import-untyped]


class RedisService:
    """Redis connection and caching service."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis: Optional[aioredis.Redis] = None  # type: ignore[type-arg]
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.redis.ping()
            print(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Bot will work without Redis cache")
            self.redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        if not self.redis:
            return False
        try:
            await self.redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False

    async def setex(self, key: str, expire: int, value: Any) -> bool:
        """Set value with expiration time."""
        return await self.set(key, value, expire=expire)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(
        self, key: str, value: Any, expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire=expire)
        except (TypeError, json.JSONDecodeError) as e:
            print(f"Redis SET_JSON error: {e}")
            return False

    async def incr(self, key: str) -> int:
        """Increment value in Redis."""
        if not self.redis:
            return 0
        try:
            return await self.redis.incr(key)
        except Exception as e:
            print(f"Redis INCR error: {e}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if not self.redis:
            return False
        try:
            await self.redis.expire(key, seconds)
            return True
        except Exception as e:
            print(f"Redis EXPIRE error: {e}")
            return False

    async def smembers(self, key: str) -> set:
        """Get set members."""
        if not self.redis:
            return set()
        try:
            result = await self.redis.smembers(key)
            return set(result) if result else set()
        except Exception as e:
            print(f"Redis SMEMBERS error: {e}")
            return set()

    async def sadd(self, key: str, *values) -> int:
        """Add member(s) to set."""
        if not self.redis:
            return 0
        try:
            return await self.redis.sadd(key, *values)
        except Exception as e:
            print(f"Redis SADD error: {e}")
            return 0

    async def srem(self, key: str, *values) -> int:
        """Remove member(s) from set."""
        if not self.redis:
            return 0
        try:
            return await self.redis.srem(key, *values)
        except Exception as e:
            print(f"Redis SREM error: {e}")
            return 0


# Global Redis instance
redis_service = RedisService()


def get_redis_client():
    """Get the global Redis client instance."""
    return redis_service
