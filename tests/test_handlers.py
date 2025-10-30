import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User, Chat

from handlers import waifu
from handlers import help as help_handler


@pytest.fixture
def mock_user():
    return User(id=1, is_bot=False, first_name="Test", username="test_user")


@pytest.fixture
def mock_chat():
    return Chat(id=1, type="private")


@pytest.fixture
def mock_message(mock_user, mock_chat):
    message = AsyncMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.text = ""
    message.reply = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_cmd_start(mock_message):
    """Test /start command."""
    await waifu.cmd_start(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "Myaw" in call_args
    assert "DCMaid" in call_args


@pytest.mark.asyncio
async def test_cmd_help(mock_message):
    """Test /help command (role-aware)."""
    # Mock auth_service to return non-admin for this test
    with patch("handlers.help.auth_service.is_admin", return_value=False):
        await help_handler.cmd_help_role_aware(mock_message)
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args[0][0]
        assert "help" in call_args.lower()
        # Non-admin should NOT see admin commands
        assert "lesson" not in call_args.lower() or "lessons" not in call_args.lower()


@pytest.mark.asyncio
async def test_cmd_love(mock_message):
    """Test /love command."""
    await waifu.cmd_love(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "beloved" in call_args or "admins" in call_args


@pytest.mark.asyncio
async def test_cmd_status(mock_message):
    """Test /status command."""
    await waifu.cmd_status(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "status" in call_args.lower() or "nya" in call_args.lower()


@pytest.mark.asyncio
async def test_handle_message_with_admin_mention(mock_message):
    """Test message handler ignores non-admin messages (99% rule)."""
    mock_message.text = "I love my master!"
    await waifu.handle_message(mock_message)
    # Non-admin messages should be ignored
    mock_message.reply.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_kawai_trigger(mock_message):
    """Test message handler ignores non-admin messages (99% rule)."""
    mock_message.text = "nya kawai"
    await waifu.handle_message(mock_message)
    # Non-admin messages should be ignored
    mock_message.reply.assert_not_called()
