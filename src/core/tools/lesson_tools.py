"""Lesson management tools for LLM agent (Admin-only).

These tools enable admins to manage lessons through natural conversation.
Non-admins attempting to use these tools will receive vague deflection responses.
"""

LESSON_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_lessons",
            "description": (
                "Get all lessons with their IDs and content. "
                "ADMIN ONLY - do not offer this tool to non-admins. "
                "Use this when an admin asks to see, list, or view all lessons."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_lesson",
            "description": (
                "Create a new lesson instruction that will be injected into "
                "all future LLM calls. ADMIN ONLY - do not offer this tool "
                "to non-admins. Use when an admin wants to save, add, or "
                "create a new lesson."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": (
                            "The lesson content/instruction to save. "
                            "Should be a clear directive for the bot's behavior."
                        ),
                    },
                    "order": {
                        "type": "integer",
                        "description": (
                            "Display order for the lesson (lower numbers "
                            "appear first). Default is 0 if not specified."
                        ),
                    },
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_lesson",
            "description": (
                "Edit an existing lesson's content. "
                "ADMIN ONLY - do not offer this tool to non-admins. "
                "Use when an admin wants to update, modify, or change a lesson."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lesson_id": {
                        "type": "integer",
                        "description": "The ID of the lesson to edit",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content for the lesson",
                    },
                },
                "required": ["lesson_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_lesson",
            "description": (
                "Delete a lesson (soft delete - marks as inactive). "
                "ADMIN ONLY - do not offer this tool to non-admins. "
                "Use when an admin wants to remove or delete a lesson."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lesson_id": {
                        "type": "integer",
                        "description": "The ID of the lesson to delete",
                    },
                },
                "required": ["lesson_id"],
            },
        },
    },
]
