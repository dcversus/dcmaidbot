"""Unit tests for nudge_handler."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from handlers.nudge import nudge_handler


@pytest.fixture
def mock_env_secret(monkeypatch):
    """Mock NUDGE_SECRET environment variable."""
    monkeypatch.setenv("NUDGE_SECRET", "test_nudge_secret")


@pytest.fixture
def mock_request():
    """Create a mock aiohttp Request."""
    request = MagicMock(spec=web.Request)
    request.headers = {}
    request.json = AsyncMock()
    return request


@pytest.mark.asyncio
async def test_nudge_handler_direct_mode_success(mock_request, mock_env_secret):
    """Test successful nudge request in direct mode."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test **direct** message with [markdown](https://example.com)",
            "type": "direct",
        }
    )

    mock_result = {
        "success": True,
        "mode": "direct",
        "sent_count": 2,
        "failed_count": 0,
        "results": [
            {"user_id": 123, "message_id": 456, "status": "success"},
            {"user_id": 789, "message_id": 101, "status": "success"},
        ],
        "errors": None,
    }

    with patch(
        "handlers.nudge.nudge_service.send_direct",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await nudge_handler(mock_request)

        assert response.status == 200
        response_data = json.loads(response.body)
        assert response_data["status"] == "success"
        assert "Message sent via direct mode" in response_data["message"]
        assert response_data["result"] == mock_result


@pytest.mark.asyncio
async def test_nudge_handler_llm_mode_success(mock_request, mock_env_secret):
    """Test successful nudge request in llm mode."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Hey! Phase 2 is complete! All tests passing! Nya~",
            "type": "llm",
        }
    )

    mock_result = {
        "success": True,
        "mode": "llm",
        "sent_count": 1,
        "failed_count": 0,
        "results": [
            {
                "user_id": 123,
                "message_id": 456,
                "llm_response": "Nya~ Masters! Phase 2 is done! 🎉",
                "status": "success",
            },
        ],
        "errors": None,
    }

    with patch(
        "handlers.nudge.nudge_service.send_via_llm",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await nudge_handler(mock_request)

        assert response.status == 200
        response_data = json.loads(response.body)
        assert response_data["status"] == "success"
        assert "Message sent via llm mode" in response_data["message"]
        assert response_data["result"] == mock_result


@pytest.mark.asyncio
async def test_nudge_handler_with_specific_user_id(mock_request, mock_env_secret):
    """Test handler sends to specific user_id when provided."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test message to specific user",
            "type": "direct",
            "user_id": 99999,
        }
    )

    mock_result = {
        "success": True,
        "mode": "direct",
        "sent_count": 1,
        "failed_count": 0,
        "results": [{"user_id": 99999, "message_id": 111, "status": "success"}],
        "errors": None,
    }

    with patch(
        "handlers.nudge.nudge_service.send_direct",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock_send:
        response = await nudge_handler(mock_request)

        assert response.status == 200
        # Verify send_direct was called with user_id
        mock_send.assert_called_once_with(
            message="Test message to specific user",
            user_id=99999,
        )


@pytest.mark.asyncio
async def test_nudge_handler_missing_nudge_secret(mock_request, monkeypatch):
    """Test handler returns 500 when NUDGE_SECRET not configured."""
    monkeypatch.delenv("NUDGE_SECRET", raising=False)

    mock_request.headers = {"Authorization": "Bearer some_token"}

    response = await nudge_handler(mock_request)

    assert response.status == 500
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "not configured" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_missing_auth_header(mock_request, mock_env_secret):
    """Test handler returns 401 when Authorization header missing."""
    mock_request.headers = {}  # No Authorization header

    response = await nudge_handler(mock_request)

    assert response.status == 401
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "Invalid authorization header format" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_auth_format(mock_request, mock_env_secret):
    """Test handler returns 401 for invalid auth header format."""
    mock_request.headers = {"Authorization": "InvalidFormat token123"}

    response = await nudge_handler(mock_request)

    assert response.status == 401
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"


@pytest.mark.asyncio
async def test_nudge_handler_wrong_token(mock_request, mock_env_secret):
    """Test handler returns 401 for incorrect token."""
    mock_request.headers = {"Authorization": "Bearer wrong_token"}

    response = await nudge_handler(mock_request)

    assert response.status == 401
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "Invalid authorization token" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_json(mock_request, mock_env_secret):
    """Test handler returns 400 for invalid JSON."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(side_effect=Exception("Invalid JSON"))

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "Invalid JSON" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_missing_message(mock_request, mock_env_secret):
    """Test handler returns 400 when message missing."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "type": "direct",
            # message missing
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "message" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_message_type(mock_request, mock_env_secret):
    """Test handler returns 400 when message is not a string."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": 12345,  # Should be string
            "type": "direct",
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "message" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_missing_type(mock_request, mock_env_secret):
    """Test handler returns 400 when type missing."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test message",
            # type missing
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "type" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_type_value(mock_request, mock_env_secret):
    """Test handler returns 400 when type is not 'direct' or 'llm'."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test message",
            "type": "invalid_type",  # Should be 'direct' or 'llm'
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "type" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_user_id_type(mock_request, mock_env_secret):
    """Test handler returns 400 when user_id is not an integer."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test message",
            "type": "direct",
            "user_id": "not_an_integer",  # Should be int
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "user_id" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_service_error(mock_request, mock_env_secret):
    """Test handler returns 500 when service throws error."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test",
            "type": "direct",
        }
    )

    with patch(
        "handlers.nudge.nudge_service.send_direct",
        new_callable=AsyncMock,
        side_effect=Exception("Bot token invalid"),
    ):
        response = await nudge_handler(mock_request)

        assert response.status == 500
        response_data = json.loads(response.body)
        assert response_data["status"] == "error"
        assert "Failed to send message" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_markdown_message(mock_request, mock_env_secret):
    """Test handler accepts and forwards markdown-formatted messages."""
    markdown_message = (
        "🎉 **PRP-005 Complete!**\n\n"
        "[View PR #15](https://github.com/dcversus/dcmaidbot/pull/15)\n\n"
        "All tests passing, ready for review! nya~"
    )

    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": markdown_message,
            "type": "direct",
        }
    )

    mock_result = {
        "success": True,
        "mode": "direct",
        "sent_count": 1,
        "failed_count": 0,
        "results": [{"user_id": 123, "message_id": 456, "status": "success"}],
        "errors": None,
    }

    with patch(
        "handlers.nudge.nudge_service.send_direct",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock_send:
        response = await nudge_handler(mock_request)

        assert response.status == 200
        # Verify markdown message was passed correctly
        mock_send.assert_called_once_with(
            message=markdown_message,
            user_id=None,
        )
