"""Tool execution handler for LLM agent calls.

This executor processes tool calls from the LLM and returns results.
Includes role-based access control for admin-only tools.
"""

import logging
import random
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.memory_service import MemoryService
from services.llm_service import LLMService
from services.lesson_service import LessonService
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Variety of vague deflection messages to prevent pattern recognition
VAGUE_DEFLECTIONS = [
    (
        "I'm not sure what you mean by that! 😊 "
        "Is there something else I can help you with?"
    ),
    "Hmm, I don't quite understand! 💭 What else would you like to know?",
    "That's a bit confusing to me! 🤔 Can I help with something different?",
    "I'm not familiar with that! 😅 What else can I do for you?",
    "I don't know about that one! 🌸 Anything else I can assist with?",
]


class ToolExecutor:
    """Execute tools requested by LLM agent."""

    def __init__(self, session: AsyncSession):
        """
        Initialize tool executor.

        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
        self.memory_service = MemoryService(session)
        self.lesson_service = LessonService(session)
        self.auth_service = AuthService()
        self.llm_service = LLMService()

    async def execute(
        self, tool_name: str, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """
        Execute a tool and return result.

        Includes role-based access control: admin-only tools will return
        a vague deflection message if called by non-admins.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from LLM
            user_id: Telegram user ID for context

        Returns:
            dict: Result of tool execution with success status and data
        """
        logger.info(
            f"Executing tool: {tool_name} with args: {arguments} for user: {user_id}"
        )

        # Check if tool is admin-only
        is_admin = self.auth_service.is_admin(user_id)
        if self.auth_service.is_admin_only_tool(tool_name) and not is_admin:
            # Non-admin trying to use admin tool - vague deflection
            logger.warning(
                f"Non-admin user {user_id} attempted to use admin tool: {tool_name}"
            )
            return {
                "success": False,
                "error": "access_denied",
                "vague_message": random.choice(VAGUE_DEFLECTIONS),
            }

        try:
            # Memory tools
            if tool_name == "create_memory":
                return await self._execute_create_memory(arguments, user_id)
            elif tool_name == "search_memories":
                return await self._execute_search_memories(arguments, user_id)
            elif tool_name == "get_memory":
                return await self._execute_get_memory(arguments, user_id)

            # Web search tool
            elif tool_name == "web_search":
                return await self._execute_web_search(arguments)

            # Lesson tools (admin-only)
            elif tool_name == "get_all_lessons":
                return await self._execute_get_all_lessons()
            elif tool_name == "create_lesson":
                return await self._execute_create_lesson(arguments, user_id)
            elif tool_name == "edit_lesson":
                return await self._execute_edit_lesson(arguments)
            elif tool_name == "delete_lesson":
                return await self._execute_delete_lesson(arguments)

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
            }

    async def _execute_create_memory(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_memory tool."""
        content = arguments.get("content")
        categories = arguments.get("categories", [])
        importance = arguments.get("importance")

        if not content:
            return {"success": False, "error": "Content is required"}

        # Generate simple content using LLM
        simple_content = await self.llm_service.extract_simple_content(content)

        # Calculate importance if not provided
        if importance is None:
            importance = await self.llm_service.calculate_importance(content)

        # Extract VAD emotions
        vad_scores = await self.llm_service.extract_vad_emotions(content)

        # Generate Zettelkasten attributes
        zettel_attrs = await self.llm_service.generate_zettelkasten_attributes(content)

        # Get category IDs from category names
        from models.memory import Category
        from sqlalchemy import select

        category_ids = []
        if categories:
            for cat_name in categories:
                result = await self.session.execute(
                    select(Category).where(Category.full_path == cat_name)
                )
                category = result.scalar_one_or_none()
                if category:
                    category_ids.append(category.id)

        # Create memory
        memory = await self.memory_service.create_memory(
            simple_content=simple_content,
            full_content=content,
            importance=importance,
            created_by=user_id,
            category_ids=category_ids if category_ids else None,
            emotion_valence=vad_scores.get("valence"),
            emotion_arousal=vad_scores.get("arousal"),
            emotion_dominance=vad_scores.get("dominance"),
            emotion_label=vad_scores.get("emotion_label"),
            keywords=zettel_attrs.get("keywords"),
            tags=zettel_attrs.get("tags"),
            context_temporal=zettel_attrs.get("temporal_context"),
            context_situational=zettel_attrs.get("situational_context"),
        )

        return {
            "success": True,
            "memory_id": memory.id,
            "message": (
                f"Memory created with ID {memory.id}. "
                f"Importance: {importance}, Categories: {categories}"
            ),
            "simple_content": simple_content,
        }

    async def _execute_search_memories(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute search_memories tool."""
        query = arguments.get("query")
        categories = arguments.get("categories")
        limit = arguments.get("limit", 10)

        if not query:
            return {"success": False, "error": "Query is required"}

        # Get category IDs if categories specified
        from models.memory import Category
        from sqlalchemy import select

        category_ids = None
        if categories:
            category_ids = []
            for cat_name in categories:
                result = await self.session.execute(
                    select(Category).where(Category.full_path == cat_name)
                )
                category = result.scalar_one_or_none()
                if category:
                    category_ids.append(category.id)

        # Search memories
        memories = await self.memory_service.search_memories(
            user_id=user_id,
            query=query,
            category_ids=category_ids,
            limit=limit,
        )

        return {
            "success": True,
            "count": len(memories),
            "memories": [
                {
                    "id": m.id,
                    "content": m.simple_content,
                    "importance": m.importance,
                    "categories": [c.full_path for c in m.categories],
                    "keywords": m.keywords,
                }
                for m in memories
            ],
        }

    async def _execute_get_memory(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_memory tool."""
        memory_id = arguments.get("memory_id")
        full = arguments.get("full", False)

        if memory_id is None:
            return {"success": False, "error": "memory_id is required"}

        memory = await self.memory_service.get_memory(memory_id)

        if not memory:
            return {
                "success": False,
                "error": f"Memory {memory_id} not found",
            }

        # Verify user owns this memory
        if memory.created_by != user_id:
            return {
                "success": False,
                "error": "Access denied - memory belongs to another user",
            }

        return {
            "success": True,
            "memory": {
                "id": memory.id,
                "content": memory.full_content if full else memory.simple_content,
                "importance": memory.importance,
                "categories": [c.full_path for c in memory.categories],
                "keywords": memory.keywords,
                "emotion_label": memory.emotion_label,
                "created_at": memory.created_at.isoformat(),
            },
        }

    async def _execute_web_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute web_search tool."""
        query = arguments.get("query")
        num_results = arguments.get("num_results", 3)

        if not query:
            return {"success": False, "error": "Query is required"}

        # Limit to max 10 results
        num_results = min(num_results, 10)

        try:
            # Use duckduckgo-search library
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "link": r.get("link", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ],
            }
        except Exception as e:
            logger.error(f"Web search error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Web search failed: {str(e)}",
            }

    async def _execute_get_all_lessons(self) -> dict[str, Any]:
        """Execute get_all_lessons tool (admin-only).

        Returns all active lessons with IDs for admin management.
        """
        try:
            lessons = await self.lesson_service.get_all_with_ids()

            if not lessons:
                return {
                    "success": True,
                    "count": 0,
                    "message": "No lessons configured yet.",
                    "lessons": [],
                }

            lessons_data = [
                {
                    "id": lesson.id,
                    "content": lesson.content,
                    "order": lesson.order,
                    "created_at": lesson.created_at.isoformat(),
                }
                for lesson in lessons
            ]

            return {
                "success": True,
                "count": len(lessons),
                "message": f"Found {len(lessons)} lesson(s)",
                "lessons": lessons_data,
            }
        except Exception as e:
            logger.error(f"Error getting lessons: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get lessons: {str(e)}",
            }

    async def _execute_create_lesson(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_lesson tool (admin-only).

        Creates a new lesson instruction.
        """
        content = arguments.get("content")
        order = arguments.get("order", 0)

        if not content:
            return {
                "success": False,
                "error": "Content is required for creating a lesson",
            }

        try:
            lesson = await self.lesson_service.add_lesson(
                content=content, admin_id=user_id, order=order
            )

            return {
                "success": True,
                "lesson_id": lesson.id,
                "message": (
                    f"✅ Lesson #{lesson.id} created successfully! "
                    f"I'll remember this instruction now."
                ),
                "lesson": {
                    "id": lesson.id,
                    "content": lesson.content,
                    "order": lesson.order,
                },
            }
        except Exception as e:
            logger.error(f"Error creating lesson: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to create lesson: {str(e)}",
            }

    async def _execute_edit_lesson(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute edit_lesson tool (admin-only).

        Edits an existing lesson's content.
        """
        lesson_id = arguments.get("lesson_id")
        content = arguments.get("content")

        if lesson_id is None:
            return {
                "success": False,
                "error": "lesson_id is required",
            }

        if not content:
            return {
                "success": False,
                "error": "content is required",
            }

        try:
            lesson = await self.lesson_service.edit_lesson(lesson_id, content)

            if not lesson:
                return {
                    "success": False,
                    "error": f"Lesson #{lesson_id} not found",
                }

            return {
                "success": True,
                "lesson_id": lesson.id,
                "message": (
                    f"✅ Lesson #{lesson.id} updated successfully! "
                    f"I'll use the new instruction now."
                ),
                "lesson": {
                    "id": lesson.id,
                    "content": lesson.content,
                    "order": lesson.order,
                },
            }
        except Exception as e:
            logger.error(f"Error editing lesson: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to edit lesson: {str(e)}",
            }

    async def _execute_delete_lesson(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute delete_lesson tool (admin-only).

        Deletes a lesson (soft delete - marks as inactive).
        """
        lesson_id = arguments.get("lesson_id")

        if lesson_id is None:
            return {
                "success": False,
                "error": "lesson_id is required",
            }

        try:
            success = await self.lesson_service.remove_lesson(lesson_id)

            if not success:
                return {
                    "success": False,
                    "error": f"Lesson #{lesson_id} not found",
                }

            return {
                "success": True,
                "lesson_id": lesson_id,
                "message": f"✅ Lesson #{lesson_id} deleted successfully!",
            }
        except Exception as e:
            logger.error(f"Error deleting lesson: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to delete lesson: {str(e)}",
            }
