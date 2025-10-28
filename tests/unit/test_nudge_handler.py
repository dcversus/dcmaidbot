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
async def test_nudge_handler_success(mock_request, mock_env_secret):
    """Test successful nudge request."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": [123456],
            "message": "Test nudge message",
            "urgency": "medium",
        }
    )

    mock_external_response = {"status": "sent", "message_id": "msg_123"}

    with patch(
        "handlers.nudge.nudge_service.forward_nudge",
        new_callable=AsyncMock,
        return_value=mock_external_response,
    ):
        response = await nudge_handler(mock_request)

        assert response.status == 200
        response_data = json.loads(response.body)
        assert response_data["status"] == "success"
        assert "Nudge forwarded" in response_data["message"]
        assert response_data["user_ids"] == [123456]
        assert response_data["external_response"] == mock_external_response


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
async def test_nudge_handler_missing_user_ids(mock_request, mock_env_secret):
    """Test handler returns 400 when user_ids missing."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "message": "Test message",
            # user_ids missing
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "user_ids" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_invalid_user_ids_type(mock_request, mock_env_secret):
    """Test handler returns 400 when user_ids is not a list."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": "not_a_list",  # Should be list
            "message": "Test message",
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "user_ids" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_missing_message(mock_request, mock_env_secret):
    """Test handler returns 400 when message missing."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": [123],
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
            "user_ids": [123],
            "message": 12345,  # Should be string
        }
    )

    response = await nudge_handler(mock_request)

    assert response.status == 400
    response_data = json.loads(response.body)
    assert response_data["status"] == "error"
    assert "message" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_with_optional_params(mock_request, mock_env_secret):
    """Test handler accepts and forwards optional parameters."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": [111, 222],
            "message": "Complex nudge",
            "pr_url": "https://github.com/test/pr/99",
            "prp_file": "PRPs/PRP-014.md",
            "prp_section": "#testing",
            "urgency": "high",
        }
    )

    mock_external_response = {"status": "sent"}

    with patch(
        "handlers.nudge.nudge_service.forward_nudge",
        new_callable=AsyncMock,
        return_value=mock_external_response,
    ) as mock_forward:
        response = await nudge_handler(mock_request)

        assert response.status == 200

        # Verify forward_nudge was called with all parameters
        mock_forward.assert_called_once_with(
            user_ids=[111, 222],
            message="Complex nudge",
            pr_url="https://github.com/test/pr/99",
            prp_file="PRPs/PRP-014.md",
            prp_section="#testing",
            urgency="high",
        )


@pytest.mark.asyncio
async def test_nudge_handler_service_error(mock_request, mock_env_secret):
    """Test handler returns 502 when service throws error."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": [123],
            "message": "Test",
        }
    )

    with patch(
        "handlers.nudge.nudge_service.forward_nudge",
        new_callable=AsyncMock,
        side_effect=Exception("External service unreachable"),
    ):
        response = await nudge_handler(mock_request)

        assert response.status == 502
        response_data = json.loads(response.body)
        assert response_data["status"] == "error"
        assert "Failed to forward nudge" in response_data["error"]


@pytest.mark.asyncio
async def test_nudge_handler_default_urgency(mock_request, mock_env_secret):
    """Test handler uses default urgency value when not provided."""
    mock_request.headers = {"Authorization": "Bearer test_nudge_secret"}
    mock_request.json = AsyncMock(
        return_value={
            "user_ids": [123],
            "message": "Test without urgency",
            # urgency not provided
        }
    )

    mock_external_response = {"status": "sent"}

    with patch(
        "handlers.nudge.nudge_service.forward_nudge",
        new_callable=AsyncMock,
        return_value=mock_external_response,
    ) as mock_forward:
        response = await nudge_handler(mock_request)

        assert response.status == 200

        # Verify default urgency was used
        call_kwargs = mock_forward.call_args.kwargs
        assert call_kwargs["urgency"] == "medium"
