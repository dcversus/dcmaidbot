"""Unit tests for NudgeService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.nudge_service import NudgeService


@pytest.fixture
def mock_env_bot_token(monkeypatch):
    """Mock BOT_TOKEN environment variable."""
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token")


@pytest.fixture
def mock_env_admin_ids(monkeypatch):
    """Mock ADMIN_IDS environment variable."""
    monkeypatch.setenv("ADMIN_IDS", "123456,789012")


@pytest.fixture
def nudge_service(mock_env_bot_token, mock_env_admin_ids):
    """Create a NudgeService instance for testing."""
    with (
        patch("services.nudge_service.Bot") as mock_bot_class,
        patch("services.nudge_service.LLMService") as mock_llm_class,
    ):
        # Mock Bot class to return a mock instance
        mock_bot_instance = AsyncMock()
        mock_bot_class.return_value = mock_bot_instance

        # Mock LLMService class to return a mock instance
        mock_llm_instance = AsyncMock()
        mock_llm_class.return_value = mock_llm_instance

        service = NudgeService()
        # Bot and LLMService are already mocked by the patches above
        yield service


@pytest.mark.asyncio
async def test_send_direct_to_all_admins(
    nudge_service,
    mock_env_admin_ids,
):
    """Test send_direct sends to all admins when user_id not specified."""
    # Mock successful send
    mock_message_1 = MagicMock()
    mock_message_1.message_id = 111
    mock_message_2 = MagicMock()
    mock_message_2.message_id = 222

    nudge_service.bot.send_message = AsyncMock(
        side_effect=[mock_message_1, mock_message_2]
    )

    result = await nudge_service.send_direct(
        message="Test message to all admins",
        user_id=None,
    )

    # Verify sent to both admins
    assert nudge_service.bot.send_message.call_count == 2
    assert result["success"] is True
    assert result["mode"] == "direct"
    assert result["sent_count"] == 2
    assert result["failed_count"] == 0
    assert len(result["results"]) == 2
    assert result["errors"] is None


@pytest.mark.asyncio
async def test_send_direct_to_specific_user(nudge_service):
    """Test send_direct sends to specific user when user_id provided."""
    mock_message = MagicMock()
    mock_message.message_id = 999

    nudge_service.bot.send_message = AsyncMock(return_value=mock_message)

    result = await nudge_service.send_direct(
        message="Test message to specific user",
        user_id=555555,
    )

    # Verify sent only to specific user
    nudge_service.bot.send_message.assert_called_once()
    call_args = nudge_service.bot.send_message.call_args

    assert call_args.kwargs["chat_id"] == 555555
    assert call_args.kwargs["text"] == "Test message to specific user"

    assert result["success"] is True
    assert result["sent_count"] == 1
    assert result["failed_count"] == 0
    assert result["results"][0]["user_id"] == 555555
    assert result["results"][0]["message_id"] == 999


@pytest.mark.asyncio
async def test_send_direct_with_markdown(nudge_service):
    """Test send_direct sends messages with Markdown formatting."""
    mock_message = MagicMock()
    mock_message.message_id = 123

    nudge_service.bot.send_message = AsyncMock(return_value=mock_message)

    markdown_text = "**Bold** and [link](https://example.com)"

    await nudge_service.send_direct(
        message=markdown_text,
        user_id=123456,
    )

    call_args = nudge_service.bot.send_message.call_args
    assert call_args.kwargs["text"] == markdown_text

    # Verify Markdown parse mode is set
    from aiogram.enums import ParseMode

    assert call_args.kwargs["parse_mode"] == ParseMode.MARKDOWN


@pytest.mark.asyncio
async def test_send_direct_handles_partial_failure(
    nudge_service,
    mock_env_admin_ids,
):
    """Test send_direct handles partial failures when sending to multiple users."""
    mock_message = MagicMock()
    mock_message.message_id = 111

    # First succeeds, second fails
    nudge_service.bot.send_message = AsyncMock(
        side_effect=[mock_message, Exception("Chat not found")]
    )

    result = await nudge_service.send_direct(
        message="Test partial failure",
        user_id=None,
    )

    assert result["success"] is False  # Not all successful
    assert result["sent_count"] == 1
    assert result["failed_count"] == 1
    assert len(result["results"]) == 1
    assert len(result["errors"]) == 1
    assert "Chat not found" in result["errors"][0]["error"]


@pytest.mark.asyncio
async def test_send_via_llm_to_all_admins(
    nudge_service,
    mock_env_admin_ids,
):
    """Test send_via_llm processes message through LLM and sends to all admins."""
    # Mock LLM responses
    nudge_service.llm_service.get_response = AsyncMock(
        side_effect=[
            "Nya~ Master 1! I have great news! 💕",
            "Nya~ Master 2! Exciting update! 🎉",
        ]
    )

    # Mock successful sends
    mock_message_1 = MagicMock()
    mock_message_1.message_id = 111
    mock_message_2 = MagicMock()
    mock_message_2.message_id = 222

    nudge_service.bot.send_message = AsyncMock(
        side_effect=[mock_message_1, mock_message_2]
    )

    result = await nudge_service.send_via_llm(
        message="Great news! Feature complete!",
        user_id=None,
    )

    # Verify LLM was called for each admin
    assert nudge_service.llm_service.get_response.call_count == 2

    # Verify messages sent
    assert nudge_service.bot.send_message.call_count == 2

    assert result["success"] is True
    assert result["mode"] == "llm"
    assert result["sent_count"] == 2
    assert result["failed_count"] == 0
    assert "llm_response" in result["results"][0]


@pytest.mark.asyncio
async def test_send_via_llm_to_specific_user(nudge_service):
    """Test send_via_llm sends personalized message to specific user."""
    nudge_service.llm_service.get_response = AsyncMock(
        return_value="Nya~ Specific user! Custom message! 💕"
    )

    mock_message = MagicMock()
    mock_message.message_id = 999

    nudge_service.bot.send_message = AsyncMock(return_value=mock_message)

    result = await nudge_service.send_via_llm(
        message="Personalized message request",
        user_id=888888,
    )

    # Verify LLM called once with correct prompt
    nudge_service.llm_service.get_response.assert_called_once()
    call_args = nudge_service.llm_service.get_response.call_args
    assert "external system" in call_args.kwargs["user_message"].lower()
    assert "Personalized message request" in call_args.kwargs["user_message"]

    # Verify message sent to correct user
    assert nudge_service.bot.send_message.call_count == 1
    send_call = nudge_service.bot.send_message.call_args
    assert send_call.kwargs["chat_id"] == 888888
    assert send_call.kwargs["text"] == "Nya~ Specific user! Custom message! 💕"

    assert result["success"] is True
    assert result["sent_count"] == 1


@pytest.mark.asyncio
async def test_send_via_llm_handles_llm_error(nudge_service):
    """Test send_via_llm handles LLM service errors."""
    nudge_service.llm_service.get_response = AsyncMock(
        side_effect=Exception("OpenAI API error")
    )

    result = await nudge_service.send_via_llm(
        message="Test LLM error handling",
        user_id=123456,
    )

    # Should record error
    assert result["success"] is False
    assert result["sent_count"] == 0
    assert result["failed_count"] == 1
    assert "OpenAI API error" in result["errors"][0]["error"]


@pytest.mark.asyncio
async def test_send_via_llm_handles_telegram_error(nudge_service):
    """Test send_via_llm handles Telegram API errors."""
    nudge_service.llm_service.get_response = AsyncMock(
        return_value="LLM response successful"
    )

    # Telegram send fails
    nudge_service.bot.send_message = AsyncMock(
        side_effect=Exception("Bot was blocked by user")
    )

    result = await nudge_service.send_via_llm(
        message="Test Telegram error handling",
        user_id=123456,
    )

    # Should record error
    assert result["success"] is False
    assert result["sent_count"] == 0
    assert result["failed_count"] == 1
    assert "Bot was blocked" in result["errors"][0]["error"]


def test_get_admin_ids_single_id(mock_env_bot_token, monkeypatch):
    """Test _get_admin_ids parses single admin ID."""
    monkeypatch.setenv("ADMIN_IDS", "123456789")

    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()
        admin_ids = service._get_admin_ids()

    assert admin_ids == [123456789]


def test_get_admin_ids_multiple_ids(mock_env_bot_token, monkeypatch):
    """Test _get_admin_ids parses multiple comma-separated admin IDs."""
    monkeypatch.setenv("ADMIN_IDS", "111,222,333")

    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()
        admin_ids = service._get_admin_ids()

    assert admin_ids == [111, 222, 333]


def test_get_admin_ids_with_spaces(mock_env_bot_token, monkeypatch):
    """Test _get_admin_ids handles spaces in admin IDs list."""
    monkeypatch.setenv("ADMIN_IDS", "111, 222 , 333")

    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()
        admin_ids = service._get_admin_ids()

    assert admin_ids == [111, 222, 333]


def test_get_admin_ids_missing_env_var(mock_env_bot_token, monkeypatch):
    """Test _get_admin_ids raises error when ADMIN_IDS not set."""
    monkeypatch.delenv("ADMIN_IDS", raising=False)

    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()

        with pytest.raises(ValueError, match="ADMIN_IDS not configured"):
            service._get_admin_ids()


def test_get_admin_ids_invalid_format(mock_env_bot_token, monkeypatch):
    """Test _get_admin_ids raises error for invalid ID format."""
    monkeypatch.setenv("ADMIN_IDS", "111,not_a_number,333")

    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()

        with pytest.raises(ValueError, match="Invalid ADMIN_IDS format"):
            service._get_admin_ids()


def test_nudge_service_init_missing_bot_token(monkeypatch):
    """Test NudgeService raises error when BOT_TOKEN not set."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(ValueError, match="BOT_TOKEN not configured"):
        NudgeService()


def test_nudge_service_init_success(mock_env_bot_token):
    """Test NudgeService initializes successfully with BOT_TOKEN."""
    with (
        patch("services.nudge_service.Bot"),
        patch("services.nudge_service.LLMService"),
    ):
        service = NudgeService()
        assert service.bot_token == "test_bot_token"
        assert service.bot is not None
        assert service.llm_service is not None
