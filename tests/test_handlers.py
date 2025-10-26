import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User, Chat

from handlers import waifu


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
    """Test /help command."""
    await waifu.cmd_help(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "help" in call_args.lower()


@pytest.mark.asyncio
async def test_cmd_love(mock_message):
    """Test /love command."""
    await waifu.cmd_love(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "Vasilisa" in call_args
    assert "Daniil" in call_args


@pytest.mark.asyncio
async def test_cmd_status(mock_message):
    """Test /status command."""
    await waifu.cmd_status(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "status" in call_args.lower() or "nya" in call_args.lower()


@pytest.mark.asyncio
async def test_handle_message_with_admin_mention(mock_message):
    """Test message handler with admin mention."""
    mock_message.text = "I love Vasilisa!"
    await waifu.handle_message(mock_message)
    mock_message.reply.assert_called_once()
    call_args = mock_message.reply.call_args[0][0]
    assert "Vasilisa" in call_args or "Daniil" in call_args


@pytest.mark.asyncio
async def test_handle_message_kawai_trigger(mock_message):
    """Test message handler with kawai trigger."""
    mock_message.text = "nya kawai"
    await waifu.handle_message(mock_message)
    mock_message.reply.assert_called_once()
