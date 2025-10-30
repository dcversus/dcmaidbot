"""Centralized authentication and authorization service.

This service provides role-based access control for dcmaidbot.
Admins are determined by the ADMIN_IDS environment variable.
"""

import os
from typing import Any, Dict, Set


class AuthService:
    """Service for authentication and role-based access control."""

    # Admin-only tools that require elevated permissions
    ADMIN_ONLY_TOOLS = {
        "get_all_lessons",
        "create_lesson",
        "edit_lesson",
        "delete_lesson",
        "reorder_lesson",
    }

    def __init__(self) -> None:
        """Initialize auth service with admin IDs from environment."""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.admin_ids: Set[int] = set(
            int(x.strip()) for x in admin_ids_str.split(",") if x.strip()
        )

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
