"""Unit tests for PRP-009 External Tools functionality."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.tool_execution import ToolExecution
from services.auth_service import AuthService
from services.tool_service import ToolService


class TestToolService:
    """Test cases for ToolService class."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        redis.incr = AsyncMock(return_value=1)
        redis.expire = AsyncMock()
        redis.smembers = AsyncMock(return_value=set())
        redis.sadd = AsyncMock()
        redis.srem = AsyncMock()
        return redis

    @pytest.fixture
    async def tool_service(self, mock_session, mock_redis):
        """Create ToolService instance with mocked dependencies."""
        with patch("services.tool_service.get_redis_client", return_value=mock_redis):
            with patch("services.tool_service.LLMService"):
                service = ToolService(mock_session)
                service.redis_client = mock_redis
                return service

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "application/json"}
        response.content = b'{"result": "success"}'
        response.text = '{"result": "success"}'
        response.json.return_value = {"result": "success"}
        response.url = "https://api.example.com/test"
        client.request.return_value = response
        return client

    @pytest.mark.asyncio
    async def test_web_search_success(self, tool_service, mock_redis):
        """Test successful web search."""
        # Mock DuckDuckGo search
        with patch("duckduckgo_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {
                    "title": "Test Result",
                    "body": "Test snippet",
                    "link": "https://example.com",
                }
            ]

            result = await tool_service.web_search(
                query="test query", num_results=5, user_id=123, chat_id=456
            )

            # ToolService.web_search returns the raw search results on success
            assert "query" in result
            assert result["query"] == "test query"
            assert "results" in result
            assert len(result["results"]) == 1
            assert result["results"][0]["title"] == "Test Result"
            assert result["results"][0]["snippet"] == "Test snippet"

            # Verify caching
            mock_redis.setex.assert_called_once()
            cache_key = mock_redis.setex.call_args[0][0]
            assert cache_key.startswith("search:")

    @pytest.mark.asyncio
    async def test_web_search_cache_hit(self, tool_service, mock_redis):
        """Test web search with cache hit."""
        cached_result = {
            "query": "test query",
            "results": [
                {
                    "title": "Cached Result",
                    "snippet": "Cached snippet",
                    "url": "https://example.com",
                }
            ],
        }
        mock_redis.get.return_value = json.dumps(cached_result)

        result = await tool_service.web_search(query="test query", user_id=123)

        # Cached results are returned as-is
        assert result["query"] == "test query"
        assert result["results"][0]["title"] == "Cached Result"

    @pytest.mark.asyncio
    async def test_web_search_rate_limiting(self, tool_service, mock_redis):
        """Test web search rate limiting."""
        # Simulate rate limit exceeded
        mock_redis.incr.return_value = 11  # Over the limit of 10

        with pytest.raises(ValueError, match="Rate limit exceeded"):
            await tool_service.web_search(query="test query", user_id=123)

    @pytest.mark.asyncio
    async def test_web_search_empty_query(self, tool_service):
        """Test web search with empty query."""
        result = await tool_service.web_search(query="")
        assert result["success"] is False
        assert "Query is required" in result["error"]

    @pytest.mark.asyncio
    async def test_curl_request_success(
        self, tool_service, mock_redis, mock_http_client
    ):
        """Test successful HTTP request."""
        tool_service.http_client = mock_http_client

        with patch.object(tool_service, "_is_allowed_url", return_value=True):
            result = await tool_service.curl_request(
                url="https://api.example.com/test",
                method="GET",
                user_id=123,
                chat_id=456,
            )

            # ToolService.curl_request returns the raw response data on success
            assert result["status_code"] == 200
            assert result["is_json"] is True
            assert result["body"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_curl_request_invalid_url(self, tool_service):
        """Test HTTP request with invalid URL."""
        result = await tool_service.curl_request(url="")
        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_curl_request_url_not_allowed(self, tool_service):
        """Test HTTP request with non-allowed URL."""
        with patch.object(tool_service, "_is_allowed_url", return_value=False):
            result = await tool_service.curl_request(url="https://blocked.example.com")
            assert result["success"] is False
            assert "URL not in allowlist" in result["error"]

    @pytest.mark.asyncio
    async def test_curl_request_response_too_large(
        self, tool_service, mock_http_client
    ):
        """Test HTTP request with response too large."""
        # Mock large response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = b"x" * 1_000_001  # Over 1MB limit
        mock_http_client.request.return_value = mock_response
        tool_service.http_client = mock_http_client

        with patch.object(tool_service, "_is_allowed_url", return_value=True):
            result = await tool_service.curl_request(
                url="https://api.example.com/large"
            )
            assert result["success"] is False
            assert "Response too large" in result["error"]

    @pytest.mark.asyncio
    async def test_url_validation_allowed_domain(self, tool_service, mock_redis):
        """Test URL validation with allowed domain."""
        mock_redis.smembers.return_value = {"api.example.com"}

        result = await tool_service._is_allowed_url("https://api.example.com/test")
        assert result is True

    @pytest.mark.asyncio
    async def test_url_validation_wildcard_domain(self, tool_service, mock_redis):
        """Test URL validation with wildcard domain."""
        mock_redis.smembers.return_value = {"*.example.com"}

        result = await tool_service._is_allowed_url("https://api.example.com/test")
        assert result is True

    @pytest.mark.asyncio
    async def test_url_validation_default_allowlist(self, tool_service, mock_redis):
        """Test URL validation with default allowlist."""
        mock_redis.smembers.return_value = set()  # No custom allowlist

        result = await tool_service._is_allowed_url("https://api.github.com/test")
        assert result is True

        # Verify default domains were added
        assert mock_redis.sadd.called

    @pytest.mark.asyncio
    async def test_add_allowed_url(self, tool_service, mock_redis):
        """Test adding allowed URL."""
        result = await tool_service.add_allowed_url("api.newdomain.com")
        assert result is True
        mock_redis.sadd.assert_called_once_with(
            "tool:url_allowlist", "api.newdomain.com"
        )

    @pytest.mark.asyncio
    async def test_remove_allowed_url(self, tool_service, mock_redis):
        """Test removing allowed URL."""
        mock_redis.srem.return_value = 1

        result = await tool_service.remove_allowed_url("api.olddomain.com")
        assert result is True
        mock_redis.srem.assert_called_once_with(
            "tool:url_allowlist", "api.olddomain.com"
        )

    @pytest.mark.asyncio
    async def test_get_allowed_urls(self, tool_service, mock_redis):
        """Test getting allowed URLs."""
        mock_redis.smembers.return_value = {b"api.example.com", b"*.github.com"}

        result = await tool_service.get_allowed_urls()
        assert set(result) == {"api.example.com", "*.github.com"}

    @pytest.mark.asyncio
    async def test_format_search_results(self, tool_service):
        """Test formatting search results with LLM."""
        with patch("services.llm_service.LLMService") as mock_llm_service:
            mock_create = AsyncMock()
            mock_create.return_value.choices[0].message.content = "Formatted results"
            mock_llm_service.return_value.client.chat.completions.create = mock_create

            tool_service.llm_service = mock_llm_service.return_value

            result = await tool_service.format_search_results(
                query="test query",
                results=[
                    {
                        "title": "Test",
                        "snippet": "Test snippet",
                        "url": "https://example.com",
                    }
                ],
            )

            assert result == "Formatted results"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_format_search_results_fallback(self, tool_service):
        """Test formatting search results when LLM fails."""
        with patch("services.llm_service.LLMService") as mock_llm_service:
            mock_create = AsyncMock()
            mock_create.side_effect = Exception("LLM error")
            mock_llm_service.return_value.client.chat.completions.create = mock_create

            tool_service.llm_service = mock_llm_service.return_value

            results = [
                {
                    "title": "Test",
                    "snippet": "Test snippet",
                    "url": "https://example.com",
                }
            ]
            result = await tool_service.format_search_results("test query", results)

            assert "Search results for 'test query'" in result
            assert "Test" in result

    @pytest.mark.asyncio
    async def test_parse_api_response(self, tool_service):
        """Test parsing API response."""
        with patch("services.llm_service.LLMService") as mock_llm_service:
            mock_create = AsyncMock()
            mock_create.return_value.choices[0].message.content = "Parsed response"
            mock_llm_service.return_value.client.chat.completions.create = mock_create

            tool_service.llm_service = mock_llm_service.return_value

            result = await tool_service.parse_api_response(
                url="https://api.example.com",
                response_body='{"data": "test"}',
                is_json=True,
            )

            assert result == "Parsed response"

    @pytest.mark.asyncio
    async def test_get_tool_usage_stats(self, tool_service, mock_session):
        """Test getting tool usage statistics."""
        # Mock database query result
        mock_execution = AsyncMock()
        mock_execution.tool_name = "web_search"
        mock_execution.success = True
        mock_execution.execution_time_ms = 100

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_execution]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await tool_service.get_tool_usage_stats(days=7)

        assert "total_executions" in result
        assert "success_rate" in result
        assert "tool_breakdown" in result
        assert result["total_executions"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_old_executions(self, tool_service, mock_session):
        """Test cleaning up old execution records."""
        mock_result = AsyncMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        result = await tool_service.cleanup_old_executions(days_to_keep=30)
        assert result == 5

    @pytest.mark.asyncio
    async def test_close_http_client(self, tool_service, mock_http_client):
        """Test closing HTTP client."""
        tool_service.http_client = mock_http_client

        await tool_service.close()
        mock_http_client.aclose.assert_called_once()


class TestAuthServiceEnhancements:
    """Test cases for AuthService enhancements for PRP-009."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        return AuthService()

    @pytest.mark.asyncio
    async def test_can_use_tool_admin_full_access(self, auth_service):
        """Test admin can use all tools."""
        auth_service.admin_ids = {123}

        result = await auth_service.can_use_tool(tool_name="web_search", user_id=123)
        assert result is True

    @pytest.mark.asyncio
    async def test_can_use_tool_public_tool(self, auth_service):
        """Test public tools can be used by anyone."""
        result = await auth_service.can_use_tool(
            tool_name="non_restricted_tool", user_id=456
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_can_use_tool_special_access_without_magic_words(self, auth_service):
        """Test special access tools require magic words."""
        result = await auth_service.can_use_tool(
            tool_name="web_search", user_id=456, message_text="please search for me"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_can_use_tool_special_access_with_magic_words(self, auth_service):
        """Test special access tools work with magic words."""
        with patch.object(auth_service, "is_friend", return_value=True):
            result = await auth_service.can_use_tool(
                tool_name="web_search",
                user_id=456,
                message_text="please kawai search for me",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_is_friend_admin_always_friend(self, auth_service):
        """Test admins are always considered friends."""
        auth_service.admin_ids = {123}

        result = await auth_service.is_friend(123)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_friend_no_memory_service(self, auth_service):
        """Test friend detection without memory service."""
        result = await auth_service.is_friend(456, memory_service=None)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_tool_access_level(self, auth_service):
        """Test getting tool access level."""
        assert auth_service.get_tool_access_level("create_lesson") == "admin"
        assert auth_service.get_tool_access_level("web_search") == "special"
        assert auth_service.get_tool_access_level("public_tool") == "public"

    @pytest.mark.asyncio
    async def test_is_admin_only_tool(self, auth_service):
        """Test checking if tool is admin-only."""
        assert auth_service.is_admin_only_tool("create_lesson") is True
        assert auth_service.is_admin_only_tool("web_search") is False
        assert auth_service.is_admin_only_tool("public_tool") is False


class TestToolExecutionModel:
    """Test cases for ToolExecution model."""

    @pytest.mark.asyncio
    async def test_tool_execution_creation(self):
        """Test creating ToolExecution record."""
        execution = ToolExecution(
            tool_name="web_search",
            user_id=123,
            chat_id=456,
            parameters='{"query": "test"}',
            success=True,
            execution_time_ms=150,
        )

        assert execution.tool_name == "web_search"
        assert execution.user_id == 123
        assert execution.chat_id == 456
        assert execution.success is True
        assert execution.execution_time_ms == 150

    @pytest.mark.asyncio
    async def test_tool_execution_with_response_data(self):
        """Test ToolExecution with response data."""
        response_data = {"results": [{"title": "Test"}]}
        execution = ToolExecution(
            tool_name="web_search",
            user_id=123,
            chat_id=456,
            parameters='{"query": "test"}',
            response_data=json.dumps(response_data),
            response_timestamp=datetime.utcnow(),
        )

        assert json.loads(execution.response_data) == response_data
        assert execution.response_timestamp is not None
