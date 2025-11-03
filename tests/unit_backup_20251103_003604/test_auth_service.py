"""Unit tests for AuthService."""

import os
from unittest.mock import patch

from services.auth_service import AuthService


def test_is_admin_with_admin_id():
    """Test is_admin returns True for admin user."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123,456,789"}):
        auth_service = AuthService()
        assert auth_service.is_admin(123) is True
        assert auth_service.is_admin(456) is True
        assert auth_service.is_admin(789) is True


def test_is_admin_with_non_admin_id():
    """Test is_admin returns False for non-admin user."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123,456,789"}):
        auth_service = AuthService()
        assert auth_service.is_admin(999) is False
        assert auth_service.is_admin(111) is False


def test_is_admin_with_empty_admin_ids():
    """Test is_admin returns False when no admins configured."""
    with patch.dict(os.environ, {"ADMIN_IDS": ""}):
        auth_service = AuthService()
        assert auth_service.is_admin(123) is False


def test_get_role_for_admin():
    """Test get_role returns 'admin' for admin user."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123"}):
        auth_service = AuthService()
        assert auth_service.get_role(123) == "admin"


def test_get_role_for_non_admin():
    """Test get_role returns 'user' for non-admin user."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123"}):
        auth_service = AuthService()
        assert auth_service.get_role(456) == "user"


def test_filter_tools_by_role_admin_sees_all():
    """Test that admins see all tools including admin-only tools."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123"}):
        auth_service = AuthService()

        all_tools = [
            {"function": {"name": "create_memory"}},
            {"function": {"name": "get_all_lessons"}},
            {"function": {"name": "create_lesson"}},
            {"function": {"name": "web_search"}},
        ]

        filtered = auth_service.filter_tools_by_role(all_tools, is_admin=True)

        assert len(filtered) == 4
        assert filtered == all_tools


def test_filter_tools_by_role_non_admin_filtered():
    """Test that non-admins don't see admin-only tools."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123"}):
        auth_service = AuthService()

        all_tools = [
            {"function": {"name": "create_memory"}},
            {"function": {"name": "get_all_lessons"}},  # Admin-only
            {"function": {"name": "create_lesson"}},  # Admin-only
            {"function": {"name": "web_search"}},
        ]

        filtered = auth_service.filter_tools_by_role(all_tools, is_admin=False)

        assert len(filtered) == 2
        tool_names = [t["function"]["name"] for t in filtered]
        assert "create_memory" in tool_names
        assert "web_search" in tool_names
        assert "get_all_lessons" not in tool_names
        assert "create_lesson" not in tool_names


def test_is_admin_only_tool():
    """Test is_admin_only_tool correctly identifies admin tools."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123"}):
        auth_service = AuthService()

        # Admin-only tools
        assert auth_service.is_admin_only_tool("get_all_lessons") is True
        assert auth_service.is_admin_only_tool("create_lesson") is True
        assert auth_service.is_admin_only_tool("edit_lesson") is True
        assert auth_service.is_admin_only_tool("delete_lesson") is True

        # Non-admin tools
        assert auth_service.is_admin_only_tool("create_memory") is False
        assert auth_service.is_admin_only_tool("search_memories") is False
        assert auth_service.is_admin_only_tool("web_search") is False


def test_admin_ids_parsing_with_spaces():
    """Test that admin IDs are parsed correctly even with spaces."""
    with patch.dict(os.environ, {"ADMIN_IDS": " 123 , 456 , 789 "}):
        auth_service = AuthService()
        assert auth_service.is_admin(123) is True
        assert auth_service.is_admin(456) is True
        assert auth_service.is_admin(789) is True


def test_admin_ids_parsing_with_empty_strings():
    """Test that empty strings in admin IDs are ignored."""
    with patch.dict(os.environ, {"ADMIN_IDS": "123,,456,,"}):
        auth_service = AuthService()
        assert auth_service.is_admin(123) is True
        assert auth_service.is_admin(456) is True
        assert len(auth_service.admin_ids) == 2
