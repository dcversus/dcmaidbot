"""E2E tests for PRP-009 External Tools integration."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from tools.tool_executor import ToolExecutor


class TestExternalToolsIntegration:
    """End-to-end tests for external tools functionality."""

    @pytest.fixture
    async def tool_executor(self):
        """Create ToolExecutor instance."""
        mock_session = AsyncMock()
        executor = ToolExecutor(mock_session)
        return executor

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user."""
        return {"id": 123456789, "is_admin": True, "is_friend": True}

    @pytest.fixture
    def mock_regular_user(self):
        """Mock regular user."""
        return {"id": 987654321, "is_admin": False, "is_friend": False}

    @pytest.fixture
    def mock_friend_user(self):
        """Mock friend user."""
        return {"id": 555666777, "is_admin": False, "is_friend": True}

    @pytest.mark.asyncio
    async def test_admin_web_search_access(self, tool_executor, mock_admin_user):
        """Test admin can use web search without restrictions."""
        with patch("duckduckgo_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {
                    "title": "Search Result",
                    "body": "Search snippet",
                    "link": "https://example.com",
                }
            ]

            result = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "test search", "num_results": 5},
                user_id=mock_admin_user["id"],
                message_text="search for test",
                chat_id=123456,
            )

            assert result["success"] is True
            assert "results" in result["data"]
            assert len(result["data"]["results"]) > 0

    @pytest.mark.asyncio
    async def test_regular_user_web_search_denied(
        self, tool_executor, mock_regular_user
    ):
        """Test regular user cannot use web search."""
        result = await tool_executor.execute(
            tool_name="web_search_enhanced",
            parameters={"query": "test search"},
            user_id=mock_regular_user["id"],
            message_text="search for test",
            chat_id=123456,
        )

        assert result["success"] is False
        assert (
            "permission" in result["error"].lower()
            or "access" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_friend_with_magic_words_web_search_access(
        self, tool_executor, mock_friend_user
    ):
        """Test friend can use web search with magic words."""
        with patch("duckduckgo_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {
                    "title": "Kawaii Result",
                    "body": "Nya snippet",
                    "link": "https://kawaii.example.com",
                }
            ]

            result = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "kawaii things"},
                user_id=mock_friend_user["id"],
                message_text="kawai please search for cute things nya",
                chat_id=123456,
            )

            assert result["success"] is True
            assert "results" in result["data"]

    @pytest.mark.asyncio
    async def test_friend_without_magic_words_web_search_denied(
        self, tool_executor, mock_friend_user
    ):
        """Test friend cannot use web search without magic words."""
        result = await tool_executor.execute(
            tool_name="web_search_enhanced",
            parameters={"query": "something"},
            user_id=mock_friend_user["id"],
            message_text="please search for something",
            chat_id=123456,
        )

        assert result["success"] is False
        assert (
            "permission" in result["error"].lower()
            or "access" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_admin_curl_request_access(self, tool_executor, mock_admin_user):
        """Test admin can use cURL requests."""
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.content = b'{"message": "success"}'
            mock_response.text = '{"message": "success"}'
            mock_response.json.return_value = {"message": "success"}
            mock_response.url = "https://api.github.com/test"
            mock_request.return_value = mock_response

            result = await tool_executor.execute(
                tool_name="curl_request_enhanced",
                parameters={"url": "https://api.github.com/test", "method": "GET"},
                user_id=mock_admin_user["id"],
                chat_id=123456,
            )

            assert result["success"] is True
            assert result["data"]["status_code"] == 200
            assert result["data"]["body"]["message"] == "success"

    @pytest.mark.asyncio
    async def test_url_allowlist_management(self, tool_executor, mock_admin_user):
        """Test URL allowlist management."""
        # Add allowed URL
        add_result = await tool_executor.execute(
            tool_name="add_allowed_url",
            parameters={"domain": "api.newservice.com"},
            user_id=mock_admin_user["id"],
        )
        assert add_result["success"] is True

        # Get allowed URLs
        get_result = await tool_executor.execute(
            tool_name="get_allowed_urls", parameters={}, user_id=mock_admin_user["id"]
        )
        assert get_result["success"] is True
        assert "api.newservice.com" in get_result["data"]["allowed_urls"]

        # Remove allowed URL
        remove_result = await tool_executor.execute(
            tool_name="remove_allowed_url",
            parameters={"domain": "api.newservice.com"},
            user_id=mock_admin_user["id"],
        )
        assert remove_result["success"] is True

    @pytest.mark.asyncio
    async def test_regular_user_url_allowlist_denied(
        self, tool_executor, mock_regular_user
    ):
        """Test regular user cannot manage URL allowlist."""
        result = await tool_executor.execute(
            tool_name="add_allowed_url",
            parameters={"domain": "malicious.com"},
            user_id=mock_regular_user["id"],
        )
        assert result["success"] is False
        assert (
            "permission" in result["error"].lower()
            or "admin" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_tool_usage_statistics(self, tool_executor, mock_admin_user):
        """Test getting tool usage statistics."""
        with patch(
            "services.tool_service.ToolService.get_tool_usage_stats"
        ) as mock_stats:
            mock_stats.return_value = {
                "total_executions": 10,
                "successful_executions": 8,
                "success_rate": 80.0,
                "average_execution_time_ms": 150.5,
                "tool_breakdown": {
                    "web_search": {"total": 6, "successful": 5},
                    "curl_request": {"total": 4, "successful": 3},
                },
            }

            result = await tool_executor.execute(
                tool_name="get_tool_usage_stats",
                parameters={"days": 7},
                user_id=mock_admin_user["id"],
            )

            assert result["success"] is True
            assert result["data"]["total_executions"] == 10
            assert result["data"]["success_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, tool_executor, mock_admin_user):
        """Test rate limiting is enforced."""
        with patch("services.tool_service.ToolService._check_rate_limit") as mock_check:
            mock_check.side_effect = ValueError(
                "Rate limit exceeded: max 10 web_search per minute"
            )

            result = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "test"},
                user_id=mock_admin_user["id"],
            )

            assert result["success"] is False
            assert "rate limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_result_caching(self, tool_executor, mock_admin_user):
        """Test search results are cached."""
        with patch("services.tool_service.ToolService.web_search") as mock_search:
            # First call
            mock_search.return_value = {
                "success": True,
                "results": [
                    {
                        "title": "Cached Result",
                        "snippet": "Test",
                        "url": "https://example.com",
                    }
                ],
            }

            result1 = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "cache test"},
                user_id=mock_admin_user["id"],
            )
            assert result1["success"] is True

            # Second call should hit cache
            result2 = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "cache test"},
                user_id=mock_admin_user["id"],
            )
            assert result2["success"] is True

            # Verify web_search was called only once due to caching
            assert mock_search.call_count == 1

    @pytest.mark.asyncio
    async def test_http_request_different_methods(self, tool_executor, mock_admin_user):
        """Test HTTP requests with different methods."""
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in methods:
            with patch("httpx.AsyncClient.request") as mock_request:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "application/json"}
                mock_response.content = b'{"method": "' + method.encode() + b'"}'
                mock_response.text = '{"method": "' + method + '"}'
                mock_response.json.return_value = {"method": method}
                mock_response.url = "https://api.example.com/test"
                mock_request.return_value = mock_response

                result = await tool_executor.execute(
                    tool_name="curl_request_enhanced",
                    parameters={
                        "url": "https://api.example.com/test",
                        "method": method,
                        "headers": {"Content-Type": "application/json"},
                        "body": '{"test": "data"}'
                        if method in ["POST", "PUT", "PATCH"]
                        else None,
                    },
                    user_id=mock_admin_user["id"],
                )

                assert result["success"] is True
                assert result["data"]["status_code"] == 200
                mock_request.assert_called_with(
                    method=method,
                    url="https://api.example.com/test",
                    headers={"Content-Type": "application/json"},
                    content=b'{"test": "data"}'
                    if method in ["POST", "PUT", "PATCH"]
                    else None,
                )

    @pytest.mark.asyncio
    async def test_error_handling_invalid_parameters(
        self, tool_executor, mock_admin_user
    ):
        """Test error handling for invalid parameters."""
        # Test missing required parameter
        result = await tool_executor.execute(
            tool_name="web_search_enhanced",
            parameters={},
            user_id=mock_admin_user["id"],
        )
        assert result["success"] is False
        assert "required" in result["error"].lower()

        # Test invalid URL
        result = await tool_executor.execute(
            tool_name="curl_request_enhanced",
            parameters={"url": "not-a-valid-url"},
            user_id=mock_admin_user["id"],
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_llm_result_formatting(self, tool_executor, mock_admin_user):
        """Test LLM-based result formatting."""
        with patch(
            "services.tool_service.ToolService.format_search_results"
        ) as mock_format:
            mock_format.return_value = (
                "🔍 **Search Results**\\n\\nHere are the formatted results..."
            )

            with patch("duckduckgo_search.DDGS") as mock_ddgs:
                mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                    {
                        "title": "Test",
                        "body": "Test snippet",
                        "link": "https://example.com",
                    }
                ]

                result = await tool_executor.execute(
                    tool_name="web_search_enhanced",
                    parameters={"query": "test formatting"},
                    user_id=mock_admin_user["id"],
                )

                assert result["success"] is True
                # Verify formatting was applied
                mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, tool_executor, mock_admin_user):
        """Test concurrent tool execution works correctly."""
        with patch("duckduckgo_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {
                    "title": f"Result {i}",
                    "body": f"Snippet {i}",
                    "link": f"https://example{i}.com",
                }
            ]

            # Execute multiple searches concurrently
            tasks = []
            for i in range(5):
                task = tool_executor.execute(
                    tool_name="web_search_enhanced",
                    parameters={"query": f"concurrent test {i}"},
                    user_id=mock_admin_user["id"],
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # All should succeed
            for i, result in enumerate(results):
                assert result["success"] is True
                assert "results" in result["data"]

    @pytest.mark.asyncio
    async def test_memory_integration_for_friend_detection(
        self, tool_executor, mock_friend_user
    ):
        """Test friend detection using memory service."""
        # Mock memory service to return friend relationship
        with patch("services.auth_service.AuthService.is_friend") as mock_is_friend:
            mock_is_friend.return_value = True

            with patch("duckduckgo_search.DDGS") as mock_ddgs:
                mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                    {
                        "title": "Friend Result",
                        "body": "Friend snippet",
                        "link": "https://friend.example.com",
                    }
                ]

                result = await tool_executor.execute(
                    tool_name="web_search_enhanced",
                    parameters={"query": "friend test"},
                    user_id=mock_friend_user["id"],
                    message_text="kawai please search for me nya",
                )

                assert result["success"] is True
                # Verify friend detection was called
                mock_is_friend.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_execution_logging(self, tool_executor, mock_admin_user):
        """Test that tool executions are properly logged."""
        with patch("services.tool_service.ToolService.web_search") as mock_search:
            mock_search.return_value = {
                "success": True,
                "results": [
                    {
                        "title": "Logged Result",
                        "snippet": "Test",
                        "url": "https://example.com",
                    }
                ],
            }

            result = await tool_executor.execute(
                tool_name="web_search_enhanced",
                parameters={"query": "logging test"},
                user_id=mock_admin_user["id"],
                chat_id=123456,
            )

            assert result["success"] is True

            # Verify the ToolService was called with correct parameters for logging
            mock_search.assert_called_once_with(
                query="logging test",
                num_results=5,
                user_id=mock_admin_user["id"],
                chat_id=123456,
            )
