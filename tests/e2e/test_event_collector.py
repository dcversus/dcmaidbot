"""E2E tests for event collection system.

Tests the complete event collection pipeline from API key creation
to event submission and processing.
"""

import secrets
from datetime import datetime, timedelta

import pytest
from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession

from models.api_key import ApiKey
from models.event import Event
from services.event_service import ApiKeyService, EventService


@pytest.fixture
async def api_key_service(async_session: AsyncSession):
    """Create API key service for testing."""
    return ApiKeyService(async_session)


@pytest.fixture
async def event_service(async_session: AsyncSession):
    """Create event service for testing."""
    return EventService(async_session)


@pytest.fixture
async def test_api_key(async_session: AsyncSession, api_key_service: ApiKeyService):
    """Create a test API key."""
    api_key, raw_key = await api_key_service.create_api_key(
        name="Test API Key",
        created_by=1,
        allowed_event_types=["button_click", "user_message"],
        rate_limit_per_minute=10,
        rate_limit_per_hour=100,
        description="API key for testing"
    )
    return api_key, raw_key


@pytest.fixture
async def inactive_api_key(async_session: AsyncSession, api_key_service: ApiKeyService):
    """Create an inactive test API key."""
    api_key, raw_key = await api_key_service.create_api_key(
        name="Inactive API Key",
        created_by=1,
        allowed_event_types=["button_click"],
        description="Inactive API key for testing"
    )
    # Deactivate the key
    await api_key_service.deactivate_api_key(api_key.id)
    return api_key, raw_key


@pytest.fixture
async def expired_api_key(async_session: AsyncSession, api_key_service: ApiKeyService):
    """Create an expired test API key."""
    api_key, raw_key = await api_key_service.create_api_key(
        name="Expired API Key",
        created_by=1,
        expires_at=datetime.utcnow() - timedelta(days=1),
        description="Expired API key for testing"
    )
    return api_key, raw_key


class TestEventCollectorE2E:
    """End-to-end tests for event collection system."""

    @pytest.mark.asyncio
    async def test_complete_event_flow(
        self,
        async_session: AsyncSession,
        api_key_service: ApiKeyService,
        event_service: EventService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test complete flow from API key creation to event processing."""
        api_key, raw_key = test_api_key

        # 1. Verify API key creation
        assert api_key.name == "Test API Key"
        assert api_key.is_active is True
        assert api_key.usage_count == 0
        assert raw_key.startswith("dcmaid_")

        # 2. Create event data
        event_data = {
            "event_id": f"test_event_{secrets.token_urlsafe(8)}",
            "user_id": 12345,
            "chat_id": 67890,
            "event_type": "button_click",
            "event_subtype": "main_menu",
            "data": {
                "button_id": "start_game",
                "screen": "main_menu",
                "timestamp": datetime.utcnow().isoformat()
            },
            "button_text": "Start Game",
            "callback_data": "action:start_game"
        }

        # 3. Submit event via HTTP API
        async with ClientSession() as session:
            headers = {"Authorization": f"Bearer {raw_key}"}
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers=headers
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert result["event_id"] == event_data["event_id"]
                assert result["status"] == "stored"

        # 4. Verify event stored in database
        stored_event = await event_service.get_event_by_id(event_data["event_id"])
        assert stored_event is not None
        assert stored_event.user_id == 12345
        assert stored_event.event_type == "button_click"
        assert stored_event.status == "unread"

        # 5. Verify API key usage updated
        await async_session.refresh(api_key)
        assert api_key.usage_count == 1
        assert api_key.last_used_at is not None

        # 6. Test event retrieval
        unread_events = await event_service.get_unread_events(limit=10)
        assert len(unread_events) >= 1
        assert any(e.event_id == event_data["event_id"] for e in unread_events)

        # 7. Test event status update
        success = await event_service.update_event_status(
            event_data["event_id"], "read"
        )
        assert success is True

        # 8. Verify status updated
        updated_event = await event_service.get_event_by_id(event_data["event_id"])
        assert updated_event.status == "read"
        assert updated_event.processed_at is not None

    @pytest.mark.asyncio
    async def test_api_key_authentication_failures(
        self,
        async_session: AsyncSession,
        test_api_key: tuple[ApiKey, str],
        inactive_api_key: tuple[ApiKey, str],
        expired_api_key: tuple[ApiKey, str]
    ):
        """Test API key authentication failure scenarios."""
        event_data = {
            "event_id": f"test_auth_{secrets.token_urlsafe(8)}",
            "user_id": 12345,
            "event_type": "button_click",
            "data": {}
        }

        async with ClientSession() as session:
            # Test invalid API key format
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers={"Authorization": "InvalidFormat"}
            ) as response:
                assert response.status == 401

            # Test non-existent API key
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers={"Authorization": "Bearer dcmaid_nonexistent"}
            ) as response:
                assert response.status == 401

            # Test inactive API key
            _, inactive_key = inactive_api_key
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers={"Authorization": f"Bearer {inactive_key}"}
            ) as response:
                assert response.status == 401

            # Test expired API key
            _, expired_key = expired_api_key
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers={"Authorization": f"Bearer {expired_key}"}
            ) as response:
                assert response.status == 401

    @pytest.mark.asyncio
    async def test_event_validation(
        self,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test event data validation."""
        _, raw_key = test_api_key
        headers = {"Authorization": f"Bearer {raw_key}"}

        async with ClientSession() as session:
            # Test missing required fields
            invalid_events = [
                {},  # Empty event
                {"user_id": 12345},  # Missing event_id and event_type
                {"event_id": "test", "event_type": "button_click"},  # Missing user_id
                {"event_id": "test", "user_id": 12345},  # Missing event_type
            ]

            for invalid_event in invalid_events:
                async with session.post(
                    "http://localhost:8080/event",
                    json=invalid_event,
                    headers=headers
                ) as response:
                    assert response.status == 400
                    result = await response.json()
                    assert "Missing required fields" in result["error"]

            # Test invalid JSON
            async with session.post(
                "http://localhost:8080/event",
                data="invalid json",
                headers=headers
            ) as response:
                assert response.status == 400

    @pytest.mark.asyncio
    async def test_duplicate_event_prevention(
        self,
        event_service: EventService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test prevention of duplicate event IDs."""
        _, raw_key = test_api_key
        event_data = {
            "event_id": f"duplicate_test_{secrets.token_urlsafe(8)}",
            "user_id": 12345,
            "event_type": "button_click",
            "data": {}
        }

        async with ClientSession() as session:
            headers = {"Authorization": f"Bearer {raw_key}"}

            # Submit first event
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers=headers
            ) as response:
                assert response.status == 200

            # Submit duplicate event
            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers=headers
            ) as response:
                assert response.status == 409
                result = await response.json()
                assert "already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_event_type_permissions(
        self,
        api_key_service: ApiKeyService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test API key event type permissions."""
        api_key, raw_key = test_api_key
        headers = {"Authorization": f"Bearer {raw_key}"}

        # Create API key with restricted permissions
        restricted_key, restricted_raw = await api_key_service.create_api_key(
            name="Restricted API Key",
            created_by=1,
            allowed_event_types=["button_click"],
            description="API key with restricted permissions"
        )
        restricted_headers = {"Authorization": f"Bearer {restricted_raw}"}

        async with ClientSession() as session:
            # Test allowed event type
            allowed_event = {
                "event_id": f"allowed_test_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "button_click",
                "data": {}
            }

            async with session.post(
                "http://localhost:8080/event",
                json=allowed_event,
                headers=restricted_headers
            ) as response:
                assert response.status == 200

            # Test forbidden event type
            forbidden_event = {
                "event_id": f"forbidden_test_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "user_message",
                "data": {}
            }

            async with session.post(
                "http://localhost:8080/event",
                json=forbidden_event,
                headers=restricted_headers
            ) as response:
                assert response.status == 403
                result = await response.json()
                assert "not authorized" in result["error"]

    @pytest.mark.asyncio
    async def test_rate_limiting(
        self,
        api_key_service: ApiKeyService
    ):
        """Test API rate limiting."""
        # Create API key with very low rate limits
        rate_limited_key, rate_limited_raw = await api_key_service.create_api_key(
            name="Rate Limited Key",
            created_by=1,
            rate_limit_per_minute=2,
            rate_limit_per_hour=5,
            description="API key for rate limiting tests"
        )
        headers = {"Authorization": f"Bearer {rate_limited_raw}"}

        async with ClientSession() as session:
            # Submit events up to the limit
            for i in range(2):
                event_data = {
                    "event_id": f"rate_test_{i}_{secrets.token_urlsafe(8)}",
                    "user_id": 12345,
                    "event_type": "button_click",
                    "data": {}
                }

                async with session.post(
                    "http://localhost:8080/event",
                    json=event_data,
                    headers=headers
                ) as response:
                    assert response.status == 200

            # Submit one more event (should be rate limited)
            event_data = {
                "event_id": f"rate_test_excess_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "button_click",
                "data": {}
            }

            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers=headers
            ) as response:
                assert response.status == 429
                result = await response.json()
                assert "Rate limit exceeded" in result["error"]
                assert "retry_after" in result

    @pytest.mark.asyncio
    async def test_cors_headers(
        self,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test CORS headers are properly set."""
        _, raw_key = test_api_key
        headers = {
            "Authorization": f"Bearer {raw_key}",
            "Origin": "https://example.com"
        }

        async with ClientSession() as session:
            # Test preflight request
            async with session.options(
                "http://localhost:8080/event",
                headers=headers
            ) as response:
                assert response.status == 200
                assert "Access-Control-Allow-Origin" in response.headers
                assert "Access-Control-Allow-Methods" in response.headers
                assert "Access-Control-Allow-Headers" in response.headers

            # Test actual request
            event_data = {
                "event_id": f"cors_test_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "button_click",
                "data": {}
            }

            async with session.post(
                "http://localhost:8080/event",
                json=event_data,
                headers=headers
            ) as response:
                assert response.status == 200
                assert "Access-Control-Allow-Origin" in response.headers

    @pytest.mark.asyncio
    async def test_event_statistics(
        self,
        event_service: EventService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test event statistics functionality."""
        # Create test events
        test_events = [
            {
                "event_id": f"stats_test_{i}_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "button_click" if i % 2 == 0 else "user_message",
                "data": {}
            }
            for i in range(5)
        ]

        for event_data in test_events:
            await event_service.create_event(**event_data)

        # Get statistics
        stats = await event_service.get_event_statistics(days=1)

        assert stats["total_events"] >= 5
        assert "button_click" in stats["event_types"]
        assert "user_message" in stats["event_types"]
        assert len(stats["event_types"]) >= 2
        assert "daily_breakdown" in stats

    @pytest.mark.asyncio
    async def test_event_search(
        self,
        event_service: EventService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test event search functionality."""
        # Create test events with searchable content
        searchable_events = [
            {
                "event_id": f"search_test_{i}_{secrets.token_urlsafe(8)}",
                "user_id": 12345,
                "event_type": "button_click",
                "button_text": "Start Adventure",
                "callback_data": f"action:adventure_{i}",
                "data": {}
            }
            for i in range(3)
        ]

        for event_data in searchable_events:
            await event_service.create_event(**event_data)

        # Search for events
        results = await event_service.search_events("Adventure")
        assert len(results) >= 3

        results = await event_service.search_events("action:adventure")
        assert len(results) >= 3

        results = await event_service.search_events("nonexistent")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_event_cleanup(
        self,
        event_service: EventService,
        test_api_key: tuple[ApiKey, str]
    ):
        """Test old event cleanup functionality."""
        # Create an old event (simulate by creating and manually updating timestamp)
        old_event = await event_service.create_event(
            event_id=f"old_test_{secrets.token_urlsafe(8)}",
            user_id=12345,
            event_type="button_click",
            data={}
        )

        # Manually update the timestamp to make it old
        from sqlalchemy import update
        await event_service.session.execute(
            update(Event)
            .where(Event.id == old_event.id)
            .values(created_at=datetime.utcnow() - timedelta(days=35))
        )
        await event_service.session.commit()

        # Run cleanup
        deleted_count = await event_service.delete_old_events(days=30)
        assert deleted_count >= 1

        # Verify old event is deleted
        deleted_event = await event_service.get_event_by_id(old_event.event_id)
        assert deleted_event is None
