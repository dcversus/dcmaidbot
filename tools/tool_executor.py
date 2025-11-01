"""Tool execution handler for LLM agent calls.

This executor processes tool calls from the LLM and returns results.
Includes role-based access control for admin-only tools and friend-based tool access.
"""

import logging
import random
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service import AuthService
from services.lesson_service import LessonService
from services.llm_service import LLMService
from services.memory_service import MemoryService
from services.tool_service import ToolService

# TelegramTools will be imported later to avoid circular import

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
        self.tool_service = ToolService(session)

        # Initialize Telegram tools (bot will be set later if available)
        self.telegram_tools = None
        self.bot = None

    def set_bot(self, bot):
        """Set the bot instance for Telegram tools."""
        self.bot = bot

    def _get_telegram_tools(self):
        """Get or create TelegramTools instance lazily."""
        if self.telegram_tools is None and self.bot is not None:
            from tools.telegram_tools import TelegramTools

            self.telegram_tools = TelegramTools(self.session, self.bot, self)
        return self.telegram_tools

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: int,
        message_text: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Execute a tool and return result.

        Includes role-based access control: admin-only tools will return
        a vague deflection message if called by non-admins.
        Special access tools require friendship and magic words.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from LLM
            user_id: Telegram user ID for context
            message_text: Original message text for friend detection
            chat_id: Telegram chat ID for logging

        Returns:
            dict: Result of tool execution with success status and data
        """
        logger.info(
            f"Executing tool: {tool_name} with args: {arguments} for user: {user_id}"
        )

        # Check access permissions
        can_use_tool = await self.auth_service.can_use_tool(
            tool_name=tool_name,
            user_id=user_id,
            message_text=message_text,
            memory_service=self.memory_service,
        )

        if not can_use_tool:
            access_level = self.auth_service.get_tool_access_level(tool_name)

            if access_level == "admin":
                # Admin-only tool - vague deflection
                logger.warning(
                    f"Non-admin user {user_id} attempted to use admin tool: {tool_name}"
                )
                return {
                    "success": False,
                    "error": "access_denied_admin",
                    "vague_message": random.choice(VAGUE_DEFLECTIONS),
                }
            elif access_level == "special":
                # Special access tool - needs friendship + magic words
                logger.warning(
                    f"User {user_id} attempted special tool without access: {tool_name}"
                )
                return {
                    "success": False,
                    "error": "access_denied_special",
                    "vague_message": random.choice(VAGUE_DEFLECTIONS),
                }

        # Special tools that use ToolService
        if tool_name == "web_search":
            return await self._execute_web_search_enhanced(arguments, user_id, chat_id)
        elif tool_name == "curl_request":
            return await self._execute_curl_request_enhanced(
                arguments, user_id, chat_id
            )
        elif tool_name == "add_allowed_url":
            return await self._execute_add_allowed_url(arguments, user_id)
        elif tool_name == "get_allowed_urls":
            return await self._execute_get_allowed_urls(arguments, user_id)
        elif tool_name == "remove_allowed_url":
            return await self._execute_remove_allowed_url(arguments, user_id)
        elif tool_name == "get_tool_stats":
            return await self._execute_get_tool_stats(arguments, user_id)

        try:
            # Memory tools
            if tool_name == "create_memory":
                return await self._execute_create_memory(arguments, user_id)
            elif tool_name == "search_memories":
                return await self._execute_search_memories(arguments, user_id)
            elif tool_name == "get_memory":
                return await self._execute_get_memory(arguments, user_id)

            # PRP-007: Semantic search and specialized retrieval tools
            elif tool_name == "semantic_search":
                return await self._execute_semantic_search(arguments, user_id)
            elif tool_name == "get_all_friends":
                return await self._execute_get_all_friends(arguments, user_id)
            elif tool_name == "get_panic_attacks":
                return await self._execute_get_panic_attacks(arguments, user_id)
            elif tool_name == "get_interests":
                return await self._execute_get_interests(arguments, user_id)
            elif tool_name == "search_by_person":
                return await self._execute_search_by_person(arguments, user_id)
            elif tool_name == "search_by_emotion":
                return await self._execute_search_by_emotion(arguments, user_id)
            elif tool_name == "search_across_versions":
                return await self._execute_search_across_versions(arguments, user_id)

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

            # Telegram rich feature tools
            elif tool_name == "send_telegram_message":
                return await self._execute_send_telegram_message(arguments, user_id)
            elif tool_name == "create_inline_keyboard":
                return await self._execute_create_inline_keyboard(arguments, user_id)
            elif tool_name == "create_reply_keyboard":
                return await self._execute_create_reply_keyboard(arguments, user_id)
            elif tool_name == "manage_events":
                return await self._execute_manage_events(arguments, user_id)
            elif tool_name == "create_api_key":
                return await self._execute_create_api_key(arguments, user_id)
            elif tool_name == "list_api_keys":
                return await self._execute_list_api_keys(arguments, user_id)
            elif tool_name == "deactivate_api_key":
                return await self._execute_deactivate_api_key(arguments, user_id)
            elif tool_name == "get_api_key_info":
                return await self._execute_get_api_key_info(arguments, user_id)
            elif tool_name == "create_nudge_token":
                return await self._execute_create_nudge_token(arguments, user_id)
            elif tool_name == "list_nudge_tokens":
                return await self._execute_list_nudge_tokens(arguments, user_id)
            elif tool_name == "deactivate_nudge_token":
                return await self._execute_deactivate_nudge_token(arguments, user_id)
            elif tool_name == "get_nudge_token_info":
                return await self._execute_get_nudge_token_info(arguments, user_id)
            elif tool_name == "game_master_action":
                return await self._execute_game_master_action(arguments, user_id)
            elif tool_name == "edit_message":
                return await self._execute_edit_message(arguments, user_id)

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
        from sqlalchemy import select

        from models.memory import Category

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
        from sqlalchemy import select

        from models.memory import Category

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

    # PRP-007: Semantic search and specialized retrieval tools execution methods

    async def _execute_semantic_search(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute semantic_search tool."""
        query = arguments.get("query")
        categories = arguments.get("categories")
        min_importance = arguments.get("min_importance", 0)
        limit = arguments.get("limit", 10)

        if not query:
            return {"success": False, "error": "Query is required"}

        try:
            memories = await self.memory_service.semantic_search(
                query=query,
                user_id=user_id,
                categories=categories,
                min_importance=min_importance,
                limit=limit,
            )

            return {
                "success": True,
                "query": query,
                "count": len(memories),
                "memories": memories,
            }
        except Exception as e:
            logger.error(f"Semantic search error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Semantic search failed: {str(e)}",
            }

    async def _execute_get_all_friends(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_all_friends tool."""
        try:
            friends = await self.memory_service.get_all_friends(user_id=user_id)

            return {
                "success": True,
                "count": len(friends),
                "friends": friends,
            }
        except Exception as e:
            logger.error(f"Get all friends error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get friends: {str(e)}",
            }

    async def _execute_get_panic_attacks(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_panic_attacks tool."""
        try:
            panic_attacks = await self.memory_service.get_panic_attacks(user_id=user_id)

            return {
                "success": True,
                "count": len(panic_attacks),
                "panic_attacks": panic_attacks,
            }
        except Exception as e:
            logger.error(f"Get panic attacks error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get panic attacks: {str(e)}",
            }

    async def _execute_get_interests(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_interests tool."""
        try:
            interests = await self.memory_service.get_interests(user_id=user_id)

            return {
                "success": True,
                "count": len(interests),
                "interests": interests,
            }
        except Exception as e:
            logger.error(f"Get interests error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get interests: {str(e)}",
            }

    async def _execute_search_by_person(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute search_by_person tool."""
        person_name = arguments.get("person_name")

        if not person_name:
            return {"success": False, "error": "person_name is required"}

        try:
            memories = await self.memory_service.search_by_person(
                user_id=user_id, person_name=person_name
            )

            return {
                "success": True,
                "person_name": person_name,
                "count": len(memories),
                "memories": memories,
            }
        except Exception as e:
            logger.error(f"Search by person error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Search by person failed: {str(e)}",
            }

    async def _execute_search_by_emotion(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute search_by_emotion tool."""
        emotion = arguments.get("emotion")

        if not emotion:
            return {"success": False, "error": "emotion is required"}

        try:
            memories = await self.memory_service.search_by_emotion(
                user_id=user_id, emotion=emotion
            )

            return {
                "success": True,
                "emotion": emotion,
                "count": len(memories),
                "memories": memories,
            }
        except Exception as e:
            logger.error(f"Search by emotion error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Search by emotion failed: {str(e)}",
            }

    async def _execute_search_across_versions(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute search_across_versions tool."""
        query = arguments.get("query")
        limit = arguments.get("limit", 10)

        if not query:
            return {"success": False, "error": "query is required"}

        try:
            memories = await self.memory_service.search_across_versions(
                user_id=user_id, query=query, limit=limit
            )

            return {
                "success": True,
                "query": query,
                "count": len(memories),
                "memories": memories,
            }
        except Exception as e:
            logger.error(f"Search across versions error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Search across versions failed: {str(e)}",
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

    # Telegram rich feature tools execution methods

    async def _execute_send_telegram_message(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute send_telegram_message tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.send_telegram_message(**arguments)

    async def _execute_create_inline_keyboard(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_inline_keyboard tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.create_inline_keyboard(**arguments)

    async def _execute_create_reply_keyboard(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_reply_keyboard tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.create_reply_keyboard(**arguments)

    async def _execute_manage_events(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute manage_events tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.manage_events(**arguments)

    async def _execute_create_api_key(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_api_key tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.create_api_key(admin_id=user_id, **arguments)

    async def _execute_list_api_keys(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute list_api_keys tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.list_api_keys(admin_id=user_id, **arguments)

    async def _execute_deactivate_api_key(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute deactivate_api_key tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.deactivate_api_key(admin_id=user_id, **arguments)

    async def _execute_get_api_key_info(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_api_key_info tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.get_api_key_info(admin_id=user_id, **arguments)

    async def _execute_create_nudge_token(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute create_nudge_token tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.create_nudge_token(admin_id=user_id, **arguments)

    async def _execute_list_nudge_tokens(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute list_nudge_tokens tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.list_nudge_tokens(admin_id=user_id, **arguments)

    async def _execute_deactivate_nudge_token(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute deactivate_nudge_token tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.deactivate_nudge_token(
            admin_id=user_id, **arguments
        )

    async def _execute_get_nudge_token_info(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_nudge_token_info tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.get_nudge_token_info(admin_id=user_id, **arguments)

    async def _execute_game_master_action(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute game_master_action tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.game_master_action(**arguments)

    async def _execute_edit_message(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute edit_message tool."""
        telegram_tools = self._get_telegram_tools()
        if not telegram_tools:
            return {
                "success": False,
                "error": "Telegram tools not available - bot not initialized",
            }

        return await telegram_tools.edit_message(**arguments)

    # PRP-009: Enhanced external tools execution methods

    async def _execute_web_search_enhanced(
        self, arguments: dict[str, Any], user_id: int, chat_id: int
    ) -> dict[str, Any]:
        """Execute enhanced web_search tool with caching and LLM formatting."""
        query = arguments.get("query")
        num_results = arguments.get("num_results", 5)
        format_results = arguments.get("format_results", False)

        if not query:
            return {"success": False, "error": "Query is required"}

        try:
            # Use ToolService for enhanced search
            results = await self.tool_service.web_search(
                query=query, num_results=num_results, user_id=user_id, chat_id=chat_id
            )

            if not results.get("success"):
                return results

            # Format results with LLM if requested
            if format_results and results.get("results"):
                formatted_summary = await self.tool_service.format_search_results(
                    query=query, results=results["results"]
                )
                results["formatted_summary"] = formatted_summary

            return results

        except Exception as e:
            logger.error(f"Enhanced web search error: {e}", exc_info=True)
            return {"success": False, "error": f"Enhanced web search failed: {str(e)}"}

    async def _execute_curl_request_enhanced(
        self, arguments: dict[str, Any], user_id: int, chat_id: int
    ) -> dict[str, Any]:
        """Execute enhanced curl_request tool with LLM response parsing."""
        url = arguments.get("url")
        method = arguments.get("method", "GET")
        headers = arguments.get("headers")
        body = arguments.get("body")
        parse_response = arguments.get("parse_response", False)

        if not url:
            return {"success": False, "error": "URL is required"}

        try:
            # Use ToolService for enhanced HTTP requests
            result = await self.tool_service.curl_request(
                url=url,
                method=method,
                headers=headers,
                body=body,
                user_id=user_id,
                chat_id=chat_id,
            )

            if not result.get("success"):
                return result

            # Parse response with LLM if requested
            if parse_response and result.get("body"):
                parsed_summary = await self.tool_service.parse_api_response(
                    url=url,
                    response_body=result["body"],
                    is_json=result.get("is_json", False),
                )
                result["parsed_summary"] = parsed_summary

            return result

        except Exception as e:
            logger.error(f"Enhanced curl request error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Enhanced curl request failed: {str(e)}",
            }

    async def _execute_add_allowed_url(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute add_allowed_url tool (admin-only)."""
        domain = arguments.get("domain")

        if not domain:
            return {"success": False, "error": "Domain is required"}

        try:
            success = await self.tool_service.add_allowed_url(domain)

            if success:
                return {
                    "success": True,
                    "message": f"✅ Added domain '{domain}' to URL allowlist.",
                    "domain": domain,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add domain '{domain}' to allowlist",
                }

        except Exception as e:
            logger.error(f"Add allowed URL error: {e}", exc_info=True)
            return {"success": False, "error": f"Add allowed URL failed: {str(e)}"}

    async def _execute_get_allowed_urls(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_allowed_urls tool (admin-only)."""
        try:
            allowed_urls = await self.tool_service.get_allowed_urls()

            return {
                "success": True,
                "count": len(allowed_urls),
                "allowed_urls": allowed_urls,
                "message": f"Found {len(allowed_urls)} allowed domain(s)",
            }

        except Exception as e:
            logger.error(f"Get allowed URLs error: {e}", exc_info=True)
            return {"success": False, "error": f"Get allowed URLs failed: {str(e)}"}

    async def _execute_remove_allowed_url(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute remove_allowed_url tool (admin-only)."""
        domain = arguments.get("domain")

        if not domain:
            return {"success": False, "error": "Domain is required"}

        try:
            removed = await self.tool_service.remove_allowed_url(domain)

            if removed:
                return {
                    "success": True,
                    "message": f"✅ Removed domain '{domain}' from URL allowlist.",
                    "domain": domain,
                }
            else:
                return {
                    "success": False,
                    "error": f"Domain '{domain}' not found in allowlist",
                }

        except Exception as e:
            logger.error(f"Remove allowed URL error: {e}", exc_info=True)
            return {"success": False, "error": f"Remove allowed URL failed: {str(e)}"}

    async def _execute_get_tool_stats(
        self, arguments: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Execute get_tool_stats tool (admin-only)."""
        tool_name = arguments.get("tool_name")
        days = arguments.get("days", 7)

        try:
            stats = await self.tool_service.get_tool_usage_stats(
                tool_name=tool_name, user_id=user_id, days=days
            )

            return {"success": True, "stats": stats}

        except Exception as e:
            logger.error(f"Get tool stats error: {e}", exc_info=True)
            return {"success": False, "error": f"Get tool stats failed: {str(e)}"}

    async def cleanup(self):
        """Cleanup resources."""
        if self.tool_service:
            await self.tool_service.close()
        logger.info("Tool executor cleaned up")
