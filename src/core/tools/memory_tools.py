"""Memory management tools for LLM agent.

These tools enable the bot to create, search, and retrieve memories
autonomously during conversations.
"""

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_memory",
            "description": (
                "Create a new memory to remember important information about "
                "the user, conversation, or facts. Use this when the user "
                "shares something important that should be remembered for "
                "future conversations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": (
                            "The full content of the memory to store. Include "
                            "all relevant context and details."
                        ),
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Categories for this memory. Choose from: "
                            "'social.person', 'social.relationship', "
                            "'knowledge.tech_domain', 'knowledge.project', "
                            "'interest.tech_preference', 'interest.humor', "
                            "'episode.event', 'episode.success', "
                            "'meta.learning'. Use multiple if applicable."
                        ),
                    },
                    "importance": {
                        "type": "integer",
                        "description": (
                            "Importance score 0-9999+. Guide: "
                            "Admins (5000+), important facts (1000-5000), "
                            "preferences (100-1000), casual info (10-100)"
                        ),
                    },
                },
                "required": ["content", "categories"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memories",
            "description": (
                "Search for relevant memories about a topic, person, or fact. "
                "Use this to recall information from past conversations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query (e.g., 'user preferences', "
                            "'Python projects', 'Vasilisa')"
                        ),
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by categories (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum memories to return (default 10)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory",
            "description": (
                "Get a specific memory by ID with full details. Use this "
                "when you need the complete content of a known memory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "The ID of the memory to retrieve",
                    },
                    "full": {
                        "type": "boolean",
                        "description": (
                            "Whether to get full content (true) or "
                            "simple summary (false). Default false."
                        ),
                    },
                },
                "required": ["memory_id"],
            },
        },
    },
]
