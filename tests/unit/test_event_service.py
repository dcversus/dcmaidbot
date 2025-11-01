"""Unit tests for Event service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.event_service import EventService


class TestEventService:
    """Test cases for EventService class."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = MagicMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        session.get = AsyncMock()
        return session

    @pytest.fixture
    def event_service(self, mock_session):
        """Create EventService instance with mock session."""
        return EventService(mock_session)

    @pytest.mark.asyncio
    async def test_create_event_success(self, event_service, mock_session):
        """Test successful event creation."""
        event_data = {
            "event_type": "button_click",
            "widget_id": "test_widget",
            "user_id": 123456789,
            "chat_id": 987654321,
            "metadata": {"button": "test_button", "page": "home"},
        }

        mock_event = MagicMock()
        mock_event.id = 1
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        with patch.object(
            event_service, "get_or_create_user", return_value=MagicMock(id=1)
        ):
            result = await event_service.create_event(**event_data)

            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_event_with_session_id(self, event_service, mock_session):
        """Test event creation with session ID."""
        event_data = {
            "event_type": "page_view",
            "session_id": "test_session_123",
            "user_id": 123456789,
            "metadata": {"page": "/home", "referrer": "/login"},
        }

        with patch.object(
            event_service, "get_or_create_user", return_value=MagicMock(id=1)
        ):
            await event_service.create_event(**event_data)

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_by_user(self, event_service, mock_session):
        """Test retrieving events by user ID."""
        user_id = 123456789
        limit = 10

        mock_events = [
            MagicMock(id=1, event_type="button_click", created_at=datetime.utcnow()),
            MagicMock(id=2, event_type="page_view", created_at=datetime.utcnow()),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result

        result = await event_service.get_events_by_user(user_id, limit=limit)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_by_session(self, event_service, mock_session):
        """Test retrieving events by session ID."""
        session_id = "test_session_123"
        limit = 20

        mock_events = [
            MagicMock(id=1, event_type="page_view", created_at=datetime.utcnow())
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result

        result = await event_service.get_events_by_session(session_id, limit=limit)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, event_service, mock_session):
        """Test retrieving events by type."""
        event_type = "button_click"
        limit = 50

        mock_events = [
            MagicMock(id=1, event_type="button_click", created_at=datetime.utcnow()),
            MagicMock(id=2, event_type="button_click", created_at=datetime.utcnow()),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result

        result = await event_service.get_events_by_type(event_type, limit=limit)

        assert len(result) == 2
        assert all(event.event_type == event_type for event in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_by_time_range(self, event_service, mock_session):
        """Test retrieving events by time range."""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        mock_events = [
            MagicMock(id=1, event_type="page_view", created_at=datetime.utcnow())
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result

        result = await event_service.get_events_by_time_range(start_time, end_time)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_event_statistics(self, event_service, mock_session):
        """Test retrieving event statistics."""
        # Mock the count queries
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 100
        mock_type_result = MagicMock()
        mock_type_result.scalars.return_value.all.return_value = [
            ("button_click", 50),
            ("page_view", 30),
            ("form_submit", 20),
        ]

        mock_session.execute.side_effect = [mock_total_result, mock_type_result]

        result = await event_service.get_event_statistics()

        assert result["total_events"] == 100
        assert len(result["by_type"]) == 3
        assert result["by_type"]["button_click"] == 50
        assert result["by_type"]["page_view"] == 30
        assert result["by_type"]["form_submit"] == 20

    @pytest.mark.asyncio
    async def test_get_recent_events(self, event_service, mock_session):
        """Test retrieving recent events."""
        limit = 5

        mock_events = [
            MagicMock(id=1, event_type="button_click", created_at=datetime.utcnow()),
            MagicMock(id=2, event_type="page_view", created_at=datetime.utcnow()),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_session.execute.return_value = mock_result

        result = await event_service.get_recent_events(limit=limit)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_events(self, event_service, mock_session):
        """Test deleting old events."""
        days_to_keep = 30
        datetime.utcnow() - timedelta(days=days_to_keep)

        mock_result = MagicMock()
        mock_result.rowcount = 15
        mock_session.execute.return_value = mock_result

        deleted_count = await event_service.delete_old_events(days_to_keep)

        assert deleted_count == 15
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_new_user(self, event_service, mock_session):
        """Test creating a new user."""
        user_id = 123456789
        mock_session.scalar.return_value = None  # User doesn't exist

        mock_user = MagicMock()
        mock_user.id = 1
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        with patch("models.user.User", return_value=mock_user):
            result = await event_service.get_or_create_user(user_id)

            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_user(self, event_service, mock_session):
        """Test retrieving an existing user."""
        user_id = 123456789
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session.scalar.return_value = mock_user

        result = await event_service.get_or_create_user(user_id)

        assert result == mock_user
        mock_session.scalar.assert_called_once()
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_event_with_validation_error(
        self, event_service, mock_session
    ):
        """Test event creation with validation error."""
        # Missing required field
        event_data = {
            "event_type": "button_click",
            # Missing user_id
        }

        with pytest.raises(ValueError, match="user_id is required"):
            await event_service.create_event(**event_data)

        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_events_with_invalid_limit(self, event_service, mock_session):
        """Test retrieving events with invalid limit."""
        user_id = 123456789

        # Test with negative limit
        result = await event_service.get_events_by_user(user_id, limit=-1)
        assert result == []

        # Test with very large limit (should be capped)
        with patch.object(event_service, "MAX_EVENTS_LIMIT", 100):
            result = await event_service.get_events_by_user(user_id, limit=1000)
            # Should use the max limit
            mock_session.execute.assert_called_once()

    def test_event_service_initialization(self, mock_session):
        """Test EventService initialization."""
        service = EventService(mock_session)
        assert service.session == mock_session
        assert hasattr(service, "MAX_EVENTS_LIMIT")

    @pytest.mark.asyncio
    async def test_batch_create_events(self, event_service, mock_session):
        """Test batch creation of events."""
        events_data = [
            {
                "event_type": "button_click",
                "user_id": 123456789,
                "metadata": {"button": "btn1"},
            },
            {
                "event_type": "page_view",
                "user_id": 123456789,
                "metadata": {"page": "/home"},
            },
        ]

        with patch.object(
            event_service, "get_or_create_user", return_value=MagicMock(id=1)
        ):
            results = await event_service.batch_create_events(events_data)

            assert len(results) == 2
            assert mock_session.add.call_count == 2
            assert mock_session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_activity_summary(self, event_service, mock_session):
        """Test getting user activity summary."""
        user_id = 123456789

        # Mock statistics query
        mock_stats_result = MagicMock()
        mock_stats_result.first.return_value = (25, 5)  # (total_events, unique_days)

        # Mock recent events
        mock_events = [
            MagicMock(id=1, event_type="button_click", created_at=datetime.utcnow())
        ]
        mock_events_result = MagicMock()
        mock_events_result.scalars.return_value.all.return_value = mock_events

        mock_session.execute.side_effect = [mock_stats_result, mock_events_result]

        result = await event_service.get_user_activity_summary(user_id)

        assert result["total_events"] == 25
        assert result["active_days"] == 5
        assert len(result["recent_events"]) == 1
