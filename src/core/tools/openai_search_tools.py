"""OpenAI web search tool for LLM agent.

This tool uses OpenAI's new Responses API with web search capability.
"""

import os
from typing import Any, Dict

from openai import AsyncOpenAI

OPENAI_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "openai_web_search",
            "description": (
                "Search the web using OpenAI's native web search tool for current information. "
                "Use this when you need to find up-to-date information, news, recent events, "
                "current documentation, or any real-time data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query (e.g., 'latest OpenAI models', 'Python 3.13 features', "
                            "'Claude Code recent updates')"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 5, max 10)",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


class OpenAISearchService:
    """Service for OpenAI web search functionality using the Responses API."""

    def __init__(self):
        """Initialize OpenAI search service."""
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Perform web search using OpenAI's Responses API with web search tool."""
        try:
            # Use OpenAI's new Responses API with web search tool
            # This is the correct API for web search as per OpenAI documentation
            response = await self.client.responses.create(
                model=os.getenv("OPENAI_SEARCH_MODEL", "gpt-4o"),
                input=query,
                tools=[
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": max_results,
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                            },
                            "required": ["query"],
                        },
                    }
                ],
                temperature=0.3,
                max_output_tokens=2000,
            )

            # Process the response
            results = []
            response_text = ""

            # Extract output from the response
            if hasattr(response, "output"):
                for output in response.output:
                    if hasattr(output, "content"):
                        results.append(
                            {
                                "type": getattr(output, "type", "text"),
                                "content": output.content,
                            }
                        )
                        response_text += output.content + "\n"

            # Also check for output_text attribute
            if hasattr(response, "output_text"):
                response_text = response.output_text

            return {
                "success": True,
                "query": query,
                "model": response.model,
                "response": response_text.strip(),
                "tool_used": True,
                "tool_name": "web_search",
                "results": results,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens
                    if hasattr(response, "usage")
                    else None,
                    "completion_tokens": response.usage.completion_tokens
                    if hasattr(response, "usage")
                    else None,
                    "total_tokens": response.usage.total_tokens
                    if hasattr(response, "usage")
                    else None,
                },
            }

        except Exception as e:
            # Check if it's an API error related to the web search tool
            error_str = str(e)
            if "responses" in error_str.lower() or "web_search" in error_str.lower():
                # The Responses API might not be available, use standard chat completion
                return await self._fallback_search(
                    query, max_results, f"Responses API error: {error_str}"
                )
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "query": query,
                }

    async def _fallback_search(
        self, query: str, max_results: int, primary_error: str = ""
    ) -> Dict[str, Any]:
        """Fallback method using chat completions with function calling."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant with web search capability. Search for and provide current information with sources.",
                    },
                    {
                        "role": "user",
                        "content": f"Search the web for: {query}\n\nPlease provide up to {max_results} relevant results with sources.",
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "description": "Search the web for current information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query",
                                    },
                                },
                                "required": ["query"],
                            },
                        },
                    }
                ],
                tool_choice="auto",
            )

            return {
                "success": True,
                "query": query,
                "model": response.model,
                "response": response.choices[0].message.content,
                "tool_used": bool(response.choices[0].message.tool_calls),
                "tool_name": "web_search",
                "fallback_mode": True,
                "primary_error": primary_error if primary_error else None,
            }

        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"Primary error: {primary_error}. Fallback error: {str(fallback_error)}",
                "query": query,
            }
