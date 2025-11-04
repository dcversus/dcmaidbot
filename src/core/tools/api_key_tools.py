"""
API Key Management Tools for LLM Integration

These tools allow the LLM to manage API keys through natural language commands.
Only available to admin users.
"""

API_KEY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_api_key",
            "description": "Create a new API key for admin access to bot endpoints",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A descriptive name for the API key",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this API key will be used for",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_api_keys",
            "description": "List all API keys with their usage statistics",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deactivate_api_key",
            "description": "Deactivate an existing API key",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_name": {
                        "type": "string",
                        "description": "The name or identifier of the API key to deactivate",
                    }
                },
                "required": ["key_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_api_key_usage",
            "description": "Check usage statistics for a specific API key",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_name": {
                        "type": "string",
                        "description": "The name of the API key to check",
                    }
                },
                "required": ["key_name"],
            },
        },
    },
]
