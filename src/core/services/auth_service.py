"""Centralized authentication and authorization service.

This service provides role-based access control for dcmaidbot.
Admins are determined by the ADMIN_IDS environment variable.
Friends are determined by memory relationships.
"""

import logging
import os
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and role-based access control."""

    # Admin-only tools that require elevated permissions
    ADMIN_ONLY_TOOLS = {
        "get_all_lessons",
        "create_lesson",
        "edit_lesson",
        "delete_lesson",
        "reorder_lesson",
        "create_api_key",
        "list_api_keys",
        "deactivate_api_key",
        "get_api_key_info",
        "create_nudge_token",
        "list_nudge_tokens",
        "deactivate_nudge_token",
        "get_nudge_token_info",
        "add_allowed_url",
        "get_allowed_urls",
        "remove_allowed_url",
    }

    # Tools that require special access (friends with kawai/nya, or admins)
    SPECIAL_ACCESS_TOOLS = {
        "web_search",
        "curl_request",
    }

    def __init__(self) -> None:
        """Initialize auth service with admin IDs from environment.

        Raises:
            Warning if ADMIN_IDS is empty or malformed (logs but doesn't fail)
        """
        admin_ids_str = os.getenv("ADMIN_IDS", "")

        # Validate and parse admin IDs
        if not admin_ids_str or not admin_ids_str.strip():
            logger.warning(
                "ADMIN_IDS environment variable is empty! "
                "No admin users will be configured."
            )
            self.admin_ids: Set[int] = set()
            return

        # Parse admin IDs with error handling
        parsed_ids: Set[int] = set()
        for id_str in admin_ids_str.split(","):
            id_str = id_str.strip()
            if not id_str:
                continue
            try:
                parsed_ids.add(int(id_str))
            except ValueError:
                logger.warning(
                    f"Invalid admin ID '{id_str}' in ADMIN_IDS - skipping. "
                    f"Admin IDs must be integers."
                )

        if not parsed_ids:
            logger.warning(
                "No valid admin IDs found in ADMIN_IDS! "
                "Check environment variable format (comma-separated integers)."
            )

        self.admin_ids = parsed_ids
        logger.info(f"AuthService initialized with {len(self.admin_ids)} admin(s)")

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin.

        Args:
            user_id: Telegram user ID to check

        Returns:
            True if user is admin, False otherwise
        """
        return user_id in self.admin_ids

    def get_role(self, user_id: int) -> str:
        """Get user role as string.

        Args:
            user_id: Telegram user ID

        Returns:
            'admin' if user is admin, 'user' otherwise
        """
        return "admin" if self.is_admin(user_id) else "user"

    async def is_friend(self, user_id: int, memory_service=None) -> bool:
        """Check if user is a friend based on memory relationships.

        Args:
            user_id: Telegram user ID to check
            memory_service: Memory service instance for friend detection

        Returns:
            True if user is identified as a friend, False otherwise
        """
        if self.is_admin(user_id):
            return True  # Admins are always friends

        if memory_service is None:
            return False  # Cannot check without memory service

        try:
            # Try to find memories with person category and high importance
            # that indicate a friend relationship
            memories = await memory_service.search_memories(
                user_id=user_id, query="friend relationship person", limit=5
            )

            # Check if any memories indicate friendship
            for memory in memories:
                content_lower = memory.simple_content.lower()
                if any(
                    word in content_lower
                    for word in ["friend", "дорог", "любимый", "close"]
                ):
                    return True

            # Also try specialized friend search
            friends = await memory_service.get_all_friends(user_id=user_id)
            return len(friends) > 0

        except Exception as e:
            logger.error(f"Error checking friend status for user {user_id}: {e}")
            return False

    async def can_use_tool(
        self,
        tool_name: str,
        user_id: int,
        message_text: Optional[str] = None,
        memory_service=None,
    ) -> bool:
        """Check if user can use a specific tool.

        Args:
            tool_name: Name of the tool
            user_id: Telegram user ID
            message_text: Message text for friend detection (optional)
            memory_service: Memory service instance (optional)

        Returns:
            True if user can use the tool, False otherwise
        """
        # Admins can use all tools
        if self.is_admin(user_id):
            return True

        # Regular users can use non-restricted tools
        if (
            tool_name not in self.ADMIN_ONLY_TOOLS
            and tool_name not in self.SPECIAL_ACCESS_TOOLS
        ):
            return True

        # Special access tools require friendship and magic words
        if tool_name in self.SPECIAL_ACCESS_TOOLS:
            if message_text:
                message_lower = message_text.lower()
                # Check for magic words
                has_magic_words = any(
                    word in message_lower for word in ["kawai", "nya", "кавай", "ня"]
                )

                if has_magic_words:
                    # Check if user is a friend
                    is_friend = await self.is_friend(user_id, memory_service)
                    return is_friend

        return False

    def get_tool_access_level(self, tool_name: str) -> str:
        """Get access level required for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            'admin' for admin-only tools,
            'special' for friend+magic-word tools,
            'public' for unrestricted tools
        """
        if tool_name in self.ADMIN_ONLY_TOOLS:
            return "admin"
        elif tool_name in self.SPECIAL_ACCESS_TOOLS:
            return "special"
        else:
            return "public"

    def filter_tools_by_role(
        self, all_tools: list[Dict[str, Any]], is_admin: bool
    ) -> list[Dict[str, Any]]:
        """Filter tools list based on user role.

        Admins see all tools. Non-admins see only non-admin tools.

        Args:
            all_tools: Full list of tool definitions
            is_admin: Whether user is admin

        Returns:
            Filtered list of tools appropriate for user's role
        """
        if is_admin:
            return all_tools  # Admins see everything

        # Filter out admin-only tools for non-admins
        return [
            tool
            for tool in all_tools
            if tool["function"]["name"] not in self.ADMIN_ONLY_TOOLS
        ]

    def is_admin_only_tool(self, tool_name: str) -> bool:
        """Check if a tool requires admin permissions.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is admin-only, False otherwise
        """
        return tool_name in self.ADMIN_ONLY_TOOLS
