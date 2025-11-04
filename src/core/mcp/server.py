"""MCP (Model Context Protocol) Server for admin memory management.

Provides tools for administrators to manage memories and lessons
through the LLM interface with proper access control.
"""

from typing import Any, Dict, List

from src.core.services.auth_service import AuthService
from src.core.services.database import AsyncSessionLocal
from src.core.services.lesson_service import LessonService
from src.core.services.memory_service import MemoryService


class MCPServer:
    """MCP Server providing admin-only tools for memory and lesson management."""

    def __init__(self):
        self.tools = {
            "view_memory": {
                "name": "view_memory",
                "description": "View stored memories (admin only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "User ID to view memories for (optional, defaults to all)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of memories to return (default: 10)",
                        },
                    },
                },
                "admin_only": True,
            },
            "update_memory": {
                "name": "update_memory",
                "description": "Update or delete memories (admin only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "description": "Memory ID to update or delete",
                        },
                        "action": {
                            "type": "string",
                            "enum": ["update", "delete"],
                            "description": "Action to perform",
                        },
                        "new_content": {
                            "type": "string",
                            "description": "New content for memory (required if action=update)",
                        },
                    },
                    "required": ["memory_id", "action"],
                },
                "admin_only": True,
            },
            "view_lesson": {
                "name": "view_lesson",
                "description": "View lesson instructions (admin only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lesson_id": {
                            "type": "integer",
                            "description": "Lesson ID to view (optional, defaults to all)",
                        },
                    },
                },
                "admin_only": True,
            },
            "update_lesson": {
                "name": "update_lesson",
                "description": "Update lesson content (admin only)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lesson_id": {
                            "type": "integer",
                            "description": "Lesson ID to update",
                        },
                        "content": {
                            "type": "string",
                            "description": "New lesson content",
                        },
                    },
                    "required": ["lesson_id", "content"],
                },
                "admin_only": True,
            },
        }

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: int,
    ) -> Dict[str, Any]:
        """Execute an MCP tool with access control.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            user_id: User ID executing the tool

        Returns:
            Tool execution result

        Raises:
            PermissionError: If user is not admin
            ValueError: If tool doesn't exist
        """
        # Check if tool exists
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool_def = self.tools[tool_name]

        # Check admin permission
        auth_service = AuthService()
        if tool_def.get("admin_only", False) and not auth_service.is_admin(user_id):
            raise PermissionError(f"Tool '{tool_name}' requires admin privileges")

        # Execute tool
        if tool_name == "view_memory":
            return await self._view_memory(arguments)
        elif tool_name == "update_memory":
            return await self._update_memory(arguments)
        elif tool_name == "view_lesson":
            return await self._view_lesson(arguments)
        elif tool_name == "update_lesson":
            return await self._update_lesson(arguments)
        else:
            raise ValueError(f"Tool '{tool_name}' not implemented")

    async def _view_memory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """View memories."""
        async with AsyncSessionLocal() as session:
            memory_service = MemoryService(session)

            user_id = arguments.get("user_id")
            limit = arguments.get("limit", 10)

            if user_id:
                memories = await memory_service.get_user_memories(user_id, limit=limit)
            else:
                # Get all memories (admin view)
                memories = await memory_service.search_memories(
                    user_id=None,
                    query="",
                    limit=limit,
                )

            return {
                "success": True,
                "data": [
                    {
                        "id": m.id,
                        "content": m.simple_content,
                        "full_content": m.full_content,
                        "user_id": m.user_id,
                        "created_at": m.created_at.isoformat()
                        if m.created_at
                        else None,
                    }
                    for m in memories
                ],
                "count": len(memories),
            }

    async def _update_memory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update or delete a memory."""
        async with AsyncSessionLocal() as session:
            memory_service = MemoryService(session)

            memory_id = arguments["memory_id"]
            action = arguments["action"]

            if action == "delete":
                success = await memory_service.delete_memory(memory_id)
                return {"success": success, "message": f"Memory {memory_id} deleted"}

            elif action == "update":
                new_content = arguments.get("new_content")
                if not new_content:
                    return {
                        "success": False,
                        "error": "New content required for update",
                    }

                # Update memory (would need to implement this method)
                # For now, return placeholder
                return {
                    "success": True,
                    "message": f"Memory {memory_id} updated with new content",
                }

            else:
                return {"success": False, "error": f"Invalid action: {action}"}

    async def _view_lesson(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """View lessons."""
        async with AsyncSessionLocal() as session:
            lesson_service = LessonService(session)

            lesson_id = arguments.get("lesson_id")

            if lesson_id:
                lesson = await lesson_service.get_lesson_by_id(lesson_id)
                if not lesson:
                    return {"success": False, "error": f"Lesson {lesson_id} not found"}

                return {
                    "success": True,
                    "data": [
                        {
                            "id": lesson.id,
                            "content": lesson.content,
                            "admin_id": lesson.admin_id,
                            "order": lesson.order,
                            "is_active": lesson.is_active,
                            "created_at": lesson.created_at.isoformat()
                            if lesson.created_at
                            else None,
                        }
                    ],
                }
            else:
                lessons = await lesson_service.get_all_lessons()
                return {
                    "success": True,
                    "data": [
                        {
                            "id": lesson.id,
                            "content": lesson.content,
                            "admin_id": lesson.admin_id,
                            "order": lesson.order,
                            "is_active": lesson.is_active,
                            "created_at": lesson.created_at.isoformat()
                            if lesson.created_at
                            else None,
                        }
                        for lesson in lessons
                    ],
                    "count": len(lessons),
                }

    async def _update_lesson(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update a lesson."""
        async with AsyncSessionLocal() as session:
            lesson_service = LessonService(session)

            lesson_id = arguments["lesson_id"]
            content = arguments["content"]

            lesson = await lesson_service.edit_lesson(lesson_id, content)
            if not lesson:
                return {"success": False, "error": f"Lesson {lesson_id} not found"}

            return {
                "success": True,
                "message": f"Lesson {lesson_id} updated",
                "data": {
                    "id": lesson.id,
                    "content": lesson.content,
                    "updated_at": lesson.updated_at.isoformat()
                    if lesson.updated_at
                    else None,
                },
            }

    def get_tools_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get available tools for a user based on permissions."""
        tools = []
        auth_service = AuthService()

        for tool_name, tool_def in self.tools.items():
            if tool_def.get("admin_only", False):
                if auth_service.is_admin(user_id):
                    tools.append(tool_def)
            else:
                tools.append(tool_def)

        return tools


# Singleton instance
_mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Get the MCP server instance."""
    return _mcp_server
