"""External Tools Service for PRP-009 - Web Search and HTTP Requests."""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.tool_execution import ToolExecution
from core.services.llm_service import LLMService
from core.services.redis_service import get_redis_client

logger = logging.getLogger(__name__)


class ToolService:
    """External tools service providing web search and HTTP request capabilities."""

    def __init__(self, session: AsyncSession):
        """Initialize tool service with database session."""
        self.session = session
        self.redis_client = get_redis_client()
        self.llm_service = LLMService()

        # Configuration
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def web_search(
        self,
        query: str,
        num_results: int = 5,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform web search and return top results with caching and rate limiting."""

        if not query or not query.strip():
            return {"success": False, "error": "Query is required"}

        # Limit results
        num_results = min(max(num_results, 1), 10)

        # Check cache first
        cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await self.redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for search query: {query[:50]}...")
            return json.loads(cached)

        # Rate limiting
        await self._check_rate_limit(user_id or 0, "web_search")

        # Log execution start
        execution = ToolExecution(
            tool_name="web_search",
            user_id=user_id or 0,
            chat_id=chat_id or 0,
            parameters=json.dumps({"query": query, "num_results": num_results}),
        )
        self.session.add(execution)
        await self.session.commit()

        start_time = time.time()

        try:
            # Use SerpAPI if available, else DuckDuckGo
            if self.serpapi_key:
                results = await self._serpapi_search(query, num_results)
            else:
                results = await self._duckduckgo_search(query, num_results)

            execution_time = int((time.time() - start_time) * 1000)

            # Update execution record
            execution.response_data = json.dumps(results)
            execution.success = True
            execution.execution_time_ms = execution_time
            execution.response_timestamp = datetime.utcnow()
            await self.session.commit()

            # Cache results for 1 hour
            await self.redis_client.setex(cache_key, 3600, json.dumps(results))

            logger.info(
                f"Web search completed in {execution_time}ms: {len(results.get('results', []))} results"
            )
            return results

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            execution.success = False
            execution.error_message = str(e)
            execution.execution_time_ms = execution_time
            execution.response_timestamp = datetime.utcnow()
            await self.session.commit()

            logger.error(f"Web search failed: {e}")
            return {"success": False, "error": f"Web search failed: {str(e)}"}

    async def _serpapi_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using SerpAPI (paid, better results)."""
        try:
            from serpapi import GoogleSearch

            search = GoogleSearch(
                {"q": query, "api_key": self.serpapi_key, "num": num_results}
            )

            results = search.get_dict()

            return {
                "query": query,
                "results": [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "url": r.get("link", ""),
                    }
                    for r in results.get("organic_results", [])[:num_results]
                ],
            }
        except ImportError:
            logger.warning("SerpAPI not available, falling back to DuckDuckGo")
            return await self._duckduckgo_search(query, num_results)

    async def _duckduckgo_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo (free alternative)."""
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))

            return {
                "query": query,
                "results": [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("link", ""),
                    }
                    for r in results
                ],
            }
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            raise

    async def curl_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to external API with validation and rate limiting."""

        if not url:
            return {"success": False, "error": "URL is required"}

        # Validate URL
        if not await self._is_allowed_url(url):
            return {"success": False, "error": f"URL not in allowlist: {url}"}

        # Rate limiting
        await self._check_rate_limit(user_id or 0, "curl_request")

        # Log execution
        execution = ToolExecution(
            tool_name="curl_request",
            user_id=user_id or 0,
            chat_id=chat_id or 0,
            parameters=json.dumps(
                {"url": url, "method": method, "headers": headers or {}, "body": body}
            ),
        )
        self.session.add(execution)
        await self.session.commit()

        start_time = time.time()

        try:
            # Prepare request
            request_headers = headers or {}
            content = body.encode() if body else None

            # Make request
            response = await self.http_client.request(
                method=method, url=url, headers=request_headers, content=content
            )

            execution_time = int((time.time() - start_time) * 1000)

            # Check response size
            if len(response.content) > 1_000_000:  # 1MB limit
                raise ValueError("Response too large (>1MB)")

            # Parse response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "is_json": False,
                "url": str(response.url),
                "execution_time_ms": execution_time,
            }

            # Try to parse as JSON
            try:
                result["body"] = response.json()
                result["is_json"] = True
            except Exception:
                # Keep as text if not JSON
                pass

            # Update execution
            execution.response_data = json.dumps(
                {
                    "status": response.status_code,
                    "size": len(response.content),
                    "url": str(response.url),
                }
            )
            execution.success = True
            execution.execution_time_ms = execution_time
            execution.response_timestamp = datetime.utcnow()
            await self.session.commit()

            logger.info(
                f"HTTP request completed: {method} {url} -> {response.status_code} ({execution_time}ms)"
            )
            return result

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            execution.success = False
            execution.error_message = str(e)
            execution.execution_time_ms = execution_time
            execution.response_timestamp = datetime.utcnow()
            await self.session.commit()

            logger.error(f"HTTP request failed: {e}")
            return {"success": False, "error": f"HTTP request failed: {str(e)}"}

    async def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is in allowlist."""
        try:
            # Get allowlist from Redis or config
            allowlist_key = "tool:url_allowlist"
            allowlist = await self.redis_client.smembers(allowlist_key)

            if not allowlist:
                # Default allowlist
                default_allowlist = [
                    "api.github.com",
                    "api.openai.com",
                    "httpbin.org",
                    "jsonplaceholder.typicode.com",
                    "*.wikipedia.org",
                    "api.githubusercontent.com",
                    "raw.githubusercontent.com",
                ]
                for domain in default_allowlist:
                    await self.redis_client.sadd(allowlist_key, domain)
                allowlist = set(default_allowlist)

            # Parse URL
            parsed = urlparse(url)
            domain = parsed.netloc

            # Check exact match or wildcard
            for allowed in allowlist:
                allowed_str = (
                    allowed.decode() if isinstance(allowed, bytes) else allowed
                )
                if allowed_str.startswith("*."):
                    # Wildcard match
                    if domain.endswith(allowed_str[2:]):
                        return True
                elif domain == allowed_str:
                    return True

            return False
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    async def _check_rate_limit(self, user_id: int, tool_name: str):
        """Check and enforce rate limiting."""
        if user_id == 0:  # Skip rate limiting for system users
            return

        rate_limit_key = f"ratelimit:{tool_name}:{user_id}"
        count = await self.redis_client.incr(rate_limit_key)

        if count == 1:
            # First request, set expiry
            await self.redis_client.expire(rate_limit_key, 60)

        if count > 10:
            raise ValueError(f"Rate limit exceeded: max 10 {tool_name} per minute")

    async def format_search_results(
        self, query: str, results: List[Dict[str, str]]
    ) -> str:
        """Format search results for LLM consumption."""
        try:
            prompt = f"""Format these web search results for the query: "{query}"

Results:
{json.dumps(results, indent=2)}

Instructions:
1. Summarize the key findings
2. Highlight most relevant information
3. Include source URLs
4. Keep under 1000 tokens
5. Write in a natural, conversational style

Return a clear, well-formatted summary."""

            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error formatting search results: {e}")
            # Return basic formatting if LLM fails
            formatted = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results[:5], 1):
                formatted += f"{i}. **{result.get('title', 'No title')}**\n"
                formatted += f"   {result.get('snippet', 'No description')}\n"
                formatted += f"   {result.get('url', 'No URL')}\n\n"
            return formatted

    async def parse_api_response(
        self, url: str, response_body: str, is_json: bool
    ) -> str:
        """Parse and summarize API response."""
        try:
            # Limit response size for LLM
            response_text = (
                response_body[:2000] if len(response_body) > 2000 else response_body
            )

            prompt = f"""Parse this API response from {url}:

Response ({"JSON" if is_json else "TEXT"}):
{response_text}

Instructions:
1. Extract key data points
2. Explain what the response means
3. Note any errors or warnings
4. Keep under 500 tokens
5. Write in a clear, helpful style

Return a clear summary."""

            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
            return f"Unable to parse response from {url}: {str(e)}"

    async def add_allowed_url(self, domain: str) -> bool:
        """Add domain to URL allowlist (admin only)."""
        try:
            await self.redis_client.sadd("tool:url_allowlist", domain)
            logger.info(f"Added domain to allowlist: {domain}")
            return True
        except Exception as e:
            logger.error(f"Error adding allowed URL: {e}")
            return False

    async def remove_allowed_url(self, domain: str) -> bool:
        """Remove domain from URL allowlist (admin only)."""
        try:
            result = await self.redis_client.srem("tool:url_allowlist", domain)
            logger.info(f"Removed domain from allowlist: {domain} (removed: {result})")
            return result > 0
        except Exception as e:
            logger.error(f"Error removing allowed URL: {e}")
            return False

    async def get_allowed_urls(self) -> List[str]:
        """Get all allowed domains."""
        try:
            allowlist = await self.redis_client.smembers("tool:url_allowlist")
            return [d.decode() if isinstance(d, bytes) else d for d in allowlist]
        except Exception as e:
            logger.error(f"Error getting allowed URLs: {e}")
            return []

    async def get_tool_usage_stats(
        self,
        tool_name: Optional[str] = None,
        user_id: Optional[int] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get tool usage statistics."""
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import select

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = select(ToolExecution)
            if tool_name:
                query = query.where(ToolExecution.tool_name == tool_name)
            if user_id:
                query = query.where(ToolExecution.user_id == user_id)
            query = query.where(ToolExecution.request_timestamp >= cutoff_date)

            result = await self.session.execute(query)
            executions = result.scalars().all()

            # Calculate statistics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.success])
            avg_execution_time = (
                sum(e.execution_time_ms or 0 for e in executions) / total_executions
                if total_executions > 0
                else 0
            )

            # Group by tool name
            tool_stats = {}
            for execution in executions:
                tool = execution.tool_name
                if tool not in tool_stats:
                    tool_stats[tool] = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "avg_time_ms": 0,
                    }

                tool_stats[tool]["total"] += 1
                if execution.success:
                    tool_stats[tool]["successful"] += 1
                else:
                    tool_stats[tool]["failed"] += 1

            return {
                "period_days": days,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": (successful_executions / total_executions * 100)
                if total_executions > 0
                else 0,
                "average_execution_time_ms": round(avg_execution_time, 2),
                "tool_breakdown": tool_stats,
            }

        except Exception as e:
            logger.error(f"Error getting tool usage stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_executions(self, days_to_keep: int = 30) -> int:
        """Clean up old tool execution records."""
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import delete

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            stmt = delete(ToolExecution).where(
                ToolExecution.request_timestamp < cutoff_date
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old tool execution records")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old executions: {e}")
            return 0

    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()
        logger.info("Tool service HTTP client closed")
