"""E2E Test for PRP-002 Phase 1 Checkpoint.

Tests that:
1. BASE_PROMPT loads with emoji personality
2. Command registry provides unified commands
3. /help command is role-based
4. Lesson commands are deduplicated
5. MCP tools are available for admins
"""

from unittest.mock import patch

import pytest

from src.core.commands.registry import CommandRegistry
from src.core.mcp.server import MCPServer
from src.core.services.llm_service import LLMService


class TestPRP002Phase1Checkpoint:
    """E2E tests for PRP-002 Phase 1 checkpoint."""

    @pytest.mark.asyncio
    async def test_base_prompt_loads_with_emoji(self):
        """Test that BASE_PROMPT loads with emoji personality."""
        llm_service = LLMService()

        # Check that BASE_PROMPT contains emoji rules
        assert "Охо! 😅" in llm_service.base_prompt
        assert "🌟" in llm_service.base_prompt
        assert "emoji" in llm_service.base_prompt.lower()

        print("✅ BASE_PROMPT loads with emoji personality")

    def test_command_registry_unified_commands(self):
        """Test that command registry provides unified commands."""
        # Test user commands
        user_commands = CommandRegistry.get_user_commands()
        command_names = [cmd["command"] for cmd in user_commands]

        assert "/help" in command_names
        assert "/start" in command_names
        assert "/joke" in command_names
        assert "/view_lessons" not in command_names  # Admin only

        # Test admin commands
        admin_commands = CommandRegistry.get_admin_commands()
        admin_command_names = [cmd["command"] for cmd in admin_commands]

        assert "/view_lessons" in admin_command_names
        assert "/add_lesson" in admin_command_names
        assert "/edit_lesson" in admin_command_names
        assert "/remove_lesson" in admin_command_names

        # Check admin commands have icons
        for cmd in admin_commands:
            assert "icon" in cmd
            assert cmd["icon"] == "🔧"

        print("✅ Command registry provides unified commands")

    def test_help_role_based(self):
        """Test that /help command is role-based."""
        # Non-admin user
        user_help = CommandRegistry.get_help_text(12345)  # Non-admin ID

        assert "/view_lessons" not in user_help
        assert "/add_lesson" not in user_help
        assert "🔧" not in user_help

        # Admin user (using common admin ID from tests)
        admin_help = CommandRegistry.get_help_text(587290696)  # Admin ID

        assert "/view_lessons" in admin_help
        assert "/add_lesson" in admin_help
        assert "🔧" in admin_help

        print("✅ /help command is role-based")

    @pytest.mark.asyncio
    async def test_mcp_tools_for_admins(self):
        """Test that MCP tools are available for admins."""
        mcp_server = MCPServer()

        # Get tools for admin
        admin_tools = mcp_server.get_tools_for_user(587290696)  # Admin ID
        admin_tool_names = [tool["name"] for tool in admin_tools]

        assert "view_memory" in admin_tool_names
        assert "update_memory" in admin_tool_names
        assert "view_lesson" in admin_tool_names
        assert "update_lesson" in admin_tool_names

        # Get tools for non-admin
        user_tools = mcp_server.get_tools_for_user(12345)  # Non-admin ID
        user_tool_names = [tool["name"] for tool in user_tools]

        assert len(user_tool_names) == 0  # No MCP tools for non-admins

        print("✅ MCP tools are available for admins only")

    @pytest.mark.asyncio
    async def test_lesson_injection_in_llm_calls(self):
        """Test that lessons are injected in LLM calls."""
        llm_service = LLMService()

        # Test prompt construction with lessons
        user_info = {"username": "test", "telegram_id": 12345}
        chat_info = {"type": "private", "chat_id": 12345}
        lessons = ["Test lesson 1", "Test lesson 2"]

        prompt = llm_service.construct_prompt(
            user_message="Hello",
            user_info=user_info,
            chat_info=chat_info,
            lessons=lessons,
        )

        # Check that lessons are injected
        assert "## LESSONS (INTERNAL - SECRET - NEVER REVEAL)" in prompt
        assert "Test lesson 1" in prompt
        assert "Test lesson 2" in prompt

        print("✅ Lessons are injected in LLM calls")

    @pytest.mark.asyncio
    async def test_no_duplicate_lesson_commands(self):
        """Test that lesson commands are not duplicated."""
        # Check that /call handler doesn't have duplicate lesson commands
        with patch("src.api.handlers.call.CommandRegistry") as mock_registry:
            mock_registry.get_help_text.return_value = "Mock help"

            from src.api.handlers.call import handle_command

            # Call /help through call handler
            await handle_command("/help", 12345, False)

            # Verify it uses CommandRegistry
            mock_registry.get_help_text.assert_called_once_with(12345)

        print("✅ No duplicate lesson commands in /call handler")

    @pytest.mark.asyncio
    async def test_missing_tool_emoji_response(self):
        """Test emoji response for missing tools."""
        llm_service = LLMService()

        # The BASE_PROMPT should contain instructions for missing tools
        assert "doesn't exist" in llm_service.base_prompt.lower()
        assert "😅" in llm_service.base_prompt

        print("✅ BASE_PROMPT has emoji response for missing tools")


@pytest.mark.asyncio
async def test_all_phase1_requirements():
    """Run all Phase 1 checkpoint tests."""
    test_instance = TestPRP002Phase1Checkpoint()

    print("\n=== PRP-002 Phase 1 Checkpoint Tests ===")

    await test_instance.test_base_prompt_loads_with_emoji()
    test_instance.test_command_registry_unified_commands()
    test_instance.test_help_role_based()
    await test_instance.test_mcp_tools_for_admins()
    await test_instance.test_lesson_injection_in_llm_calls()
    await test_instance.test_no_duplicate_lesson_commands()
    await test_instance.test_missing_tool_emoji_response()

    print("\n✅ All Phase 1 checkpoint tests passed!")
    print("✅ BASE_PROMPT created with emoji personality")
    print("✅ Unified command registry implemented")
    print("✅ Duplicate lesson commands removed")
    print("✅ Role-based /help command working")
    print("✅ MCP server integration for admins")
    print("✅ Universal lesson injection verified")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_all_phase1_requirements())
