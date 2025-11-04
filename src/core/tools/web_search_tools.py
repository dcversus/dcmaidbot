"""Web search tools for LLM agent.

These tools enable the bot to search the web for current information.
"""

WEB_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. Use this when you "
                "need to find up-to-date information that you don't have in "
                "your knowledge base (e.g., latest versions, current events, "
                "recent documentation)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query (e.g., 'latest Claude Code version', "
                            "'Python 3.12 release date')"
                        ),
                    },
                    "num_results": {
                        "type": "integer",
                        "description": (
                            "Number of search results to return (default 3, max 10)"
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
]
