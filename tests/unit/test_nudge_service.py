"""Unit tests for NudgeService."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from services.nudge_service import NudgeService


@pytest.fixture
def nudge_service():
    """Create a NudgeService instance for testing."""
    return NudgeService()


@pytest.fixture
def mock_env_secret(monkeypatch):
    """Mock NUDGE_SECRET environment variable."""
    monkeypatch.setenv("NUDGE_SECRET", "test_secret_key")


@pytest.mark.asyncio
async def test_forward_nudge_success(nudge_service, mock_env_secret):
    """Test successful nudge forwarding."""
    mock_response_data = {"status": "success", "message_sent": True}

    # Create mock response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await nudge_service.forward_nudge(
            user_ids=[123456],
            message="Test message",
            pr_url="https://github.com/test/repo/pull/1",
            urgency="high",
        )

        assert result == mock_response_data
        mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_forward_nudge_with_all_params(nudge_service, mock_env_secret):
    """Test nudge with all optional parameters."""
    mock_response_data = {"status": "success"}

    # Create mock response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await nudge_service.forward_nudge(
            user_ids=[123, 456],
            message="Complex test message",
            pr_url="https://github.com/test/pr/1",
            prp_file="PRPs/PRP-014.md",
            prp_section="#implementation",
            urgency="low",
        )

        assert result == mock_response_data


@pytest.mark.asyncio
async def test_forward_nudge_missing_secret(nudge_service, monkeypatch):
    """Test forward_nudge raises ValueError when NUDGE_SECRET not set."""
    monkeypatch.delenv("NUDGE_SECRET", raising=False)

    with pytest.raises(ValueError, match="NUDGE_SECRET not configured"):
        await nudge_service.forward_nudge(
            user_ids=[123],
            message="Test",
        )


@pytest.mark.asyncio
async def test_forward_nudge_http_error(nudge_service, mock_env_secret):
    """Test forward_nudge handles HTTP errors from external endpoint."""
    # Create mock response that raises error on raise_for_status()
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"error": "Server error"})
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        )
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ClientResponseError):
            await nudge_service.forward_nudge(
                user_ids=[123],
                message="Test",
            )


@pytest.mark.asyncio
async def test_forward_nudge_timeout(nudge_service, mock_env_secret):
    """Test forward_nudge handles timeout errors."""
    # Create mock response that raises timeout
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(
        side_effect=aiohttp.ServerTimeoutError("Timeout")
    )
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ServerTimeoutError):
            await nudge_service.forward_nudge(
                user_ids=[123],
                message="Test",
            )


@pytest.mark.asyncio
async def test_forward_nudge_connection_error(nudge_service, mock_env_secret):
    """Test forward_nudge handles connection errors."""
    # Create mock response that raises connection error
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(
        side_effect=aiohttp.ClientConnectionError("Connection refused")
    )
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ClientConnectionError):
            await nudge_service.forward_nudge(
                user_ids=[123],
                message="Test",
            )


def test_nudge_service_endpoint_constant(nudge_service):
    """Test that EXTERNAL_ENDPOINT is correctly set."""
    assert nudge_service.EXTERNAL_ENDPOINT == "https://dcmaid.theedgestory.org/nudge"


@pytest.mark.asyncio
async def test_forward_nudge_builds_correct_payload(nudge_service, mock_env_secret):
    """Test that forward_nudge builds payload correctly."""
    mock_response_data = {"status": "success"}

    # Create mock response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await nudge_service.forward_nudge(
            user_ids=[111, 222],
            message="Test payload",
            pr_url="https://test.com/pr",
            prp_file="PRPs/PRP-999.md",
            urgency="medium",
        )

        # Verify the call was made with correct endpoint
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args

        # Check endpoint URL
        assert call_args.args[0] == nudge_service.EXTERNAL_ENDPOINT

        # Check JSON payload
        payload = call_args.kwargs["json"]
        assert payload["user_ids"] == [111, 222]
        assert payload["message"] == "Test payload"
        assert payload["pr_url"] == "https://test.com/pr"
        assert payload["prp_file"] == "PRPs/PRP-999.md"
        assert payload["urgency"] == "medium"


@pytest.mark.asyncio
async def test_forward_nudge_includes_auth_header(nudge_service, mock_env_secret):
    """Test that forward_nudge includes correct Authorization header."""
    mock_response_data = {"status": "success"}

    # Create mock response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Create mock session
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await nudge_service.forward_nudge(
            user_ids=[123],
            message="Auth test",
        )

        # Verify the call was made with correct headers
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args

        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer test_secret_key"
        assert headers["Content-Type"] == "application/json"
