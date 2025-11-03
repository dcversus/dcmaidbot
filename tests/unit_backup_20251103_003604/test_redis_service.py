"""Unit tests for Redis service."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from services.redis_service import RedisService, get_redis_client, redis_service


class TestRedisService:
    """Test cases for RedisService class."""

    @pytest.fixture
    def redis_service_instance(self):
        """Create RedisService instance."""
        return RedisService()

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client."""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        return mock_redis

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_service_instance, mock_redis_client):
        """Test successful Redis connection."""
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await redis_service_instance.connect()

            assert redis_service_instance.redis == mock_redis_client
            mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, redis_service_instance):
        """Test Redis connection failure."""
        with patch(
            "redis.asyncio.from_url", side_effect=Exception("Connection failed")
        ):
            await redis_service_instance.connect()

            assert redis_service_instance.redis is None

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_service_instance, mock_redis_client):
        """Test Redis disconnection."""
        redis_service_instance.redis = mock_redis_client

        await redis_service_instance.disconnect()

        mock_redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_success(self, redis_service_instance, mock_redis_client):
        """Test successful get operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.get.return_value = "test_value"

        result = await redis_service_instance.get("test_key")

        assert result == "test_value"
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_no_redis(self, redis_service_instance):
        """Test get operation when Redis is not connected."""
        result = await redis_service_instance.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error(self, redis_service_instance, mock_redis_client):
        """Test get operation with Redis error."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.get.side_effect = Exception("Redis error")

        result = await redis_service_instance.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, redis_service_instance, mock_redis_client):
        """Test successful set operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await redis_service_instance.set("test_key", "test_value")

        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test_value", ex=None)

    @pytest.mark.asyncio
    async def test_set_with_expiry(self, redis_service_instance, mock_redis_client):
        """Test set operation with expiration."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await redis_service_instance.set("test_key", "test_value", expire=3600)

        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test_value", ex=3600)

    @pytest.mark.asyncio
    async def test_set_no_redis(self, redis_service_instance):
        """Test set operation when Redis is not connected."""
        result = await redis_service_instance.set("test_key", "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_setex(self, redis_service_instance, mock_redis_client):
        """Test setex operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await redis_service_instance.setex("test_key", 3600, "test_value")

        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test_value", ex=3600)

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_service_instance, mock_redis_client):
        """Test successful delete operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.delete.return_value = 1

        result = await redis_service_instance.delete("test_key")

        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_no_redis(self, redis_service_instance):
        """Test delete operation when Redis is not connected."""
        result = await redis_service_instance.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_json_success(self, redis_service_instance, mock_redis_client):
        """Test successful get_json operation."""
        test_data = {"key": "value", "number": 42}
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.get.return_value = json.dumps(test_data)

        result = await redis_service_instance.get_json("test_key")

        assert result == test_data

    @pytest.mark.asyncio
    async def test_get_json_invalid_json(
        self, redis_service_instance, mock_redis_client
    ):
        """Test get_json operation with invalid JSON."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.get.return_value = "invalid json"

        result = await redis_service_instance.get_json("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_no_data(self, redis_service_instance, mock_redis_client):
        """Test get_json operation with no data."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.get.return_value = None

        result = await redis_service_instance.get_json("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_json_success(self, redis_service_instance, mock_redis_client):
        """Test successful set_json operation."""
        test_data = {"key": "value", "number": 42}
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await redis_service_instance.set_json("test_key", test_data)

        assert result is True
        mock_redis_client.set.assert_called_once_with(
            "test_key", json.dumps(test_data), ex=None
        )

    @pytest.mark.asyncio
    async def test_set_json_with_expiry(
        self, redis_service_instance, mock_redis_client
    ):
        """Test set_json operation with expiration."""
        test_data = {"key": "value"}
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await redis_service_instance.set_json(
            "test_key", test_data, expire=3600
        )

        assert result is True
        mock_redis_client.set.assert_called_once_with(
            "test_key", json.dumps(test_data), ex=3600
        )

    @pytest.mark.asyncio
    async def test_set_json_serialization_error(
        self, redis_service_instance, mock_redis_client
    ):
        """Test set_json operation with serialization error."""

        # Use a non-serializable object
        def non_serializable():
            return None  # Functions can't be JSON serialized

        redis_service_instance.redis = mock_redis_client

        result = await redis_service_instance.set_json("test_key", non_serializable)

        assert result is False

    @pytest.mark.asyncio
    async def test_incr_success(self, redis_service_instance, mock_redis_client):
        """Test successful incr operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.incr.return_value = 5

        result = await redis_service_instance.incr("counter")

        assert result == 5
        mock_redis_client.incr.assert_called_once_with("counter")

    @pytest.mark.asyncio
    async def test_incr_no_redis(self, redis_service_instance):
        """Test incr operation when Redis is not connected."""
        result = await redis_service_instance.incr("counter")

        assert result == 0

    @pytest.mark.asyncio
    async def test_incr_redis_error(self, redis_service_instance, mock_redis_client):
        """Test incr operation with Redis error."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.incr.side_effect = Exception("Redis error")

        result = await redis_service_instance.incr("counter")

        assert result == 0

    @pytest.mark.asyncio
    async def test_expire_success(self, redis_service_instance, mock_redis_client):
        """Test successful expire operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.expire.return_value = True

        result = await redis_service_instance.expire("test_key", 3600)

        assert result is True
        mock_redis_client.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_expire_no_redis(self, redis_service_instance):
        """Test expire operation when Redis is not connected."""
        result = await redis_service_instance.expire("test_key", 3600)

        assert result is False

    @pytest.mark.asyncio
    async def test_smembers_success(self, redis_service_instance, mock_redis_client):
        """Test successful smembers operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.smembers.return_value = {"member1", "member2"}

        result = await redis_service_instance.smembers("test_set")

        assert result == {"member1", "member2"}
        mock_redis_client.smembers.assert_called_once_with("test_set")

    @pytest.mark.asyncio
    async def test_smembers_empty_result(
        self, redis_service_instance, mock_redis_client
    ):
        """Test smembers operation with empty result."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.smembers.return_value = set()

        result = await redis_service_instance.smembers("test_set")

        assert result == set()

    @pytest.mark.asyncio
    async def test_smembers_no_redis(self, redis_service_instance):
        """Test smembers operation when Redis is not connected."""
        result = await redis_service_instance.smembers("test_set")

        assert result == set()

    @pytest.mark.asyncio
    async def test_sadd_success(self, redis_service_instance, mock_redis_client):
        """Test successful sadd operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.sadd.return_value = 2

        result = await redis_service_instance.sadd("test_set", "member1", "member2")

        assert result == 2
        mock_redis_client.sadd.assert_called_once_with("test_set", "member1", "member2")

    @pytest.mark.asyncio
    async def test_sadd_no_redis(self, redis_service_instance):
        """Test sadd operation when Redis is not connected."""
        result = await redis_service_instance.sadd("test_set", "member1")

        assert result == 0

    @pytest.mark.asyncio
    async def test_srem_success(self, redis_service_instance, mock_redis_client):
        """Test successful srem operation."""
        redis_service_instance.redis = mock_redis_client
        mock_redis_client.srem.return_value = 1

        result = await redis_service_instance.srem("test_set", "member1")

        assert result == 1
        mock_redis_client.srem.assert_called_once_with("test_set", "member1")

    @pytest.mark.asyncio
    async def test_srem_no_redis(self, redis_service_instance):
        """Test srem operation when Redis is not connected."""
        result = await redis_service_instance.srem("test_set", "member1")

        assert result == 0

    def test_initialization(self):
        """Test RedisService initialization."""
        with patch.dict("os.environ", {"REDIS_URL": "redis://custom:6379/1"}):
            service = RedisService()
            assert service.redis_url == "redis://custom:6379/1"
            assert service.redis is None


class TestGlobalRedisInstance:
    """Test cases for global Redis instance and helper function."""

    def test_global_redis_instance_exists(self):
        """Test that global redis_service instance exists."""
        assert redis_service is not None
        assert isinstance(redis_service, RedisService)

    def test_get_redis_client(self):
        """Test get_redis_client helper function."""
        client = get_redis_client()
        assert client is redis_service

    def test_redis_service_singleton(self):
        """Test that redis_service is a singleton."""
        client1 = get_redis_client()
        client2 = get_redis_client()
        assert client1 is client2
