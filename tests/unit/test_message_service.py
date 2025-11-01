"""Unit tests for Message service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.message import Message
from services.message_service import MessageService


class TestMessageService:
    """Test cases for MessageService class."""

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
    def message_service(self, mock_session):
        """Create MessageService instance with mock session."""
        return MessageService(mock_session)

    @pytest.mark.asyncio
    async def test_create_message_success(self, message_service, mock_session):
        """Test successful message creation."""
        message_data = {
            "telegram_id": 123456,
            "user_id": 987654321,
            "chat_id": 555666777,
            "text": "Hello, world!",
            "message_type": "text",
        }

        mock_message = MagicMock()
        mock_message.id = 1
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        result = await message_service.create_message(**message_data)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_by_id(self, message_service, mock_session):
        """Test retrieving message by ID."""
        message_id = 1
        mock_message = MagicMock(
            id=message_id,
            telegram_id=123456,
            text="Test message",
            created_at=datetime.utcnow(),
        )
        mock_session.get.return_value = mock_message

        result = await message_service.get_message_by_id(message_id)

        assert result == mock_message
        mock_session.get.assert_called_once_with(Message, message_id)

    @pytest.mark.asyncio
    async def test_get_message_by_telegram_id(self, message_service, mock_session):
        """Test retrieving message by Telegram ID."""
        telegram_id = 123456
        mock_message = MagicMock(
            telegram_id=telegram_id, text="Test message", created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_message
        mock_session.execute.return_value = mock_result

        result = await message_service.get_message_by_telegram_id(telegram_id)

        assert result == mock_message
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages_by_user(self, message_service, mock_session):
        """Test retrieving messages by user ID."""
        user_id = 987654321
        limit = 10

        mock_messages = [
            MagicMock(id=1, user_id=user_id, text="Message 1"),
            MagicMock(id=2, user_id=user_id, text="Message 2"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.get_messages_by_user(user_id, limit=limit)

        assert len(result) == 2
        assert all(msg.user_id == user_id for msg in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages_by_chat(self, message_service, mock_session):
        """Test retrieving messages by chat ID."""
        chat_id = 555666777
        limit = 20

        mock_messages = [
            MagicMock(id=1, chat_id=chat_id, text="Chat message 1"),
            MagicMock(id=2, chat_id=chat_id, text="Chat message 2"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.get_messages_by_chat(chat_id, limit=limit)

        assert len(result) == 2
        assert all(msg.chat_id == chat_id for msg in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages_by_type(self, message_service, mock_session):
        """Test retrieving messages by type."""
        message_type = "command"
        limit = 50

        mock_messages = [
            MagicMock(id=1, message_type=message_type, text="/start"),
            MagicMock(id=2, message_type=message_type, text="/help"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.get_messages_by_type(message_type, limit=limit)

        assert len(result) == 2
        assert all(msg.message_type == message_type for msg in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_messages_by_content(self, message_service, mock_session):
        """Test searching messages by content."""
        search_query = "hello"
        limit = 25

        mock_messages = [
            MagicMock(id=1, text="Hello world", created_at=datetime.utcnow()),
            MagicMock(id=2, text="Say hello to everyone", created_at=datetime.utcnow()),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.search_messages_by_content(
            search_query, limit=limit
        )

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages_by_time_range(self, message_service, mock_session):
        """Test retrieving messages by time range."""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        mock_messages = [
            MagicMock(id=1, text="Recent message", created_at=datetime.utcnow())
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.get_messages_by_time_range(start_time, end_time)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_messages(self, message_service, mock_session):
        """Test retrieving recent messages."""
        limit = 5

        mock_messages = [
            MagicMock(id=1, text="Most recent", created_at=datetime.utcnow()),
            MagicMock(id=2, text="Second recent", created_at=datetime.utcnow()),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_session.execute.return_value = mock_result

        result = await message_service.get_recent_messages(limit=limit)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message(self, message_service, mock_session):
        """Test updating a message."""
        message_id = 1
        update_data = {"text": "Updated text", "edited_at": datetime.utcnow()}

        mock_message = MagicMock(id=message_id)
        mock_session.get.return_value = mock_message

        result = await message_service.update_message(message_id, **update_data)

        assert result is not None
        mock_session.get.assert_called_once_with(Message, message_id)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message_not_found(self, message_service, mock_session):
        """Test updating a non-existent message."""
        message_id = 999
        update_data = {"text": "Updated text"}

        mock_session.get.return_value = None

        result = await message_service.update_message(message_id, **update_data)

        assert result is None
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_message(self, message_service, mock_session):
        """Test deleting a message."""
        message_id = 1
        mock_message = MagicMock(id=message_id)
        mock_session.get.return_value = mock_message

        result = await message_service.delete_message(message_id)

        assert result is True
        mock_session.get.assert_called_once_with(Message, message_id)
        mock_session.delete.assert_called_once_with(mock_message)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, message_service, mock_session):
        """Test deleting a non-existent message."""
        message_id = 999
        mock_session.get.return_value = None

        result = await message_service.delete_message(message_id)

        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_message_statistics(self, message_service, mock_session):
        """Test retrieving message statistics."""
        # Mock count queries
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 500
        mock_type_result = MagicMock()
        mock_type_result.scalars.return_value.all.return_value = [
            ("text", 300),
            ("command", 150),
            ("photo", 50),
        ]
        mock_user_result = MagicMock()
        mock_user_result.scalar.return_value = 25

        mock_session.execute.side_effect = [
            mock_total_result,
            mock_type_result,
            mock_user_result,
        ]

        result = await message_service.get_message_statistics()

        assert result["total_messages"] == 500
        assert len(result["by_type"]) == 3
        assert result["by_type"]["text"] == 300
        assert result["by_type"]["command"] == 150
        assert result["by_type"]["photo"] == 50
        assert result["unique_users"] == 25

    @pytest.mark.asyncio
    async def test_delete_old_messages(self, message_service, mock_session):
        """Test deleting old messages."""
        days_to_keep = 30
        datetime.utcnow() - timedelta(days=days_to_keep)

        mock_result = MagicMock()
        mock_result.rowcount = 100
        mock_session.execute.return_value = mock_result

        deleted_count = await message_service.delete_old_messages(days_to_keep)

        assert deleted_count == 100
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_count_by_chat(self, message_service, mock_session):
        """Test getting message count by chat."""
        chat_id = 555666777

        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_session.execute.return_value = mock_result

        result = await message_service.get_message_count_by_chat(chat_id)

        assert result == 25
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_most_active_chats(self, message_service, mock_session):
        """Test getting most active chats."""
        limit = 10

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (555666777, 100),
            (888999000, 75),
            (111222333, 50),
        ]
        mock_session.execute.return_value = mock_result

        result = await message_service.get_most_active_chats(limit=limit)

        assert len(result) == 3
        assert result[0] == {"chat_id": 555666777, "message_count": 100}
        assert result[1] == {"chat_id": 888999000, "message_count": 75}
        assert result[2] == {"chat_id": 111222333, "message_count": 50}

    @pytest.mark.asyncio
    async def test_get_user_message_count(self, message_service, mock_session):
        """Test getting message count for a user."""
        user_id = 987654321

        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        mock_session.execute.return_value = mock_result

        result = await message_service.get_user_message_count(user_id)

        assert result == 15
        mock_session.execute.assert_called_once()

    def test_message_service_initialization(self, mock_session):
        """Test MessageService initialization."""
        service = MessageService(mock_session)
        assert service.session == mock_session
        assert hasattr(service, "MAX_MESSAGES_LIMIT")

    @pytest.mark.asyncio
    async def test_get_messages_with_invalid_limit(self, message_service, mock_session):
        """Test retrieving messages with invalid limit."""
        user_id = 987654321

        # Test with negative limit
        result = await message_service.get_messages_by_user(user_id, limit=-1)
        assert result == []

        # Test with very large limit (should be capped)
        with patch.object(message_service, "MAX_MESSAGES_LIMIT", 100):
            result = await message_service.get_messages_by_user(user_id, limit=1000)
            # Should use the max limit
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_with_validation_error(
        self, message_service, mock_session
    ):
        """Test message creation with validation error."""
        # Missing required field
        message_data = {
            "user_id": 987654321,
            # Missing text
        }

        with pytest.raises(ValueError, match="text is required"):
            await message_service.create_message(**message_data)

        mock_session.add.assert_not_called()
