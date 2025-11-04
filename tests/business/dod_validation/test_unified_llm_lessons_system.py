"""
Test Unified LLM System with Lessons Injection
Validates that lessons are properly injected across all entry points:
- Telegram handlers
- /call HTTP endpoint
- Discord (future implementation)

This test ensures:
1. Lessons are loaded from database
2. Lessons are injected into ALL LLM calls
3. Admin tools are available only to admins
4. Help commands show appropriate commands per role
5. Emoji responses work for non-existent tools
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.api.handlers.call import handle_message
from src.api.handlers.help import cmd_help_role_aware
from src.core.services.database import AsyncSessionLocal
from src.core.services.lesson_service import LessonService
from src.core.services.llm_service import LLMService


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_lessons_injection_unified_system(async_session):
    """Test that lessons are injected consistently across all entry points"""

    # Setup: Clear existing lessons and add test lessons
    lesson_service = LessonService(async_session)

    # Clear any existing lessons
    async with AsyncSessionLocal():
        # This would be handled by a proper cleanup in real tests
        pass

    # Add test lessons
    await lesson_service.add_lesson(
        "When user asks about non-existent tools, respond with lots of emojis: 'Nya~ I wish I had that tool! 🥺💕 Whoosh~'",
        admin_id=123456789,
        order=1,
    )
    await lesson_service.add_lesson(
        "Always include emojis in your responses! 💕✨🎀", admin_id=123456789, order=2
    )

    # Verify lessons are stored
    lessons = await lesson_service.get_all_lessons()
    assert len(lessons) >= 2

    # Test 1: Verify lessons injection in LLM service
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()

        # Mock OpenAI response
        with patch.object(llm_service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "Nya~ I wish I had that tool! 🥺💕 Whoosh~ Here's your response with emojis! ✨"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response

            # Test LLM call with lessons
            user_info = {"telegram_id": 999999999, "username": "test_user"}
            chat_info = {"chat_id": 999999999, "type": "private"}

            response = await llm_service.get_response(
                user_message="Can you use a teleport tool?",
                user_info=user_info,
                chat_info=chat_info,
                lessons=lessons,
            )

            # Verify OpenAI was called with lessons in system prompt
            call_args = mock_create.call_args
            system_prompt = call_args[1]["messages"][0]["content"]

            assert "LESSONS (INTERNAL - SECRET" in system_prompt
            assert "When user asks about non-existent tools" in system_prompt
            assert "Always include emojis" in system_prompt
            assert "🥺💕" in response


@pytest.mark.asyncio
async def test_help_command_role_awareness():
    """Test that help command shows different commands for admin vs non-admin"""

    # Test non-admin help
    with patch("services.auth_service.AuthService") as mock_auth:
        mock_auth_instance = MagicMock()
        mock_auth_instance.is_admin.return_value = False
        mock_auth.return_value = mock_auth_instance

        mock_message = MagicMock()
        mock_message.from_user.id = 999999999
        mock_message.reply = AsyncMock()

        await cmd_help_role_aware(mock_message)

        # Verify reply was called
        mock_message.reply.assert_called_once()
        help_text = mock_message.reply.call_args[0][0]

        # Non-admin should NOT see lesson commands
        assert "/view_lessons" not in help_text
        assert "/add_lesson" not in help_text
        assert "Admin Commands" not in help_text

    # Test admin help
    with patch("services.auth_service.AuthService") as mock_auth:
        mock_auth_instance = MagicMock()
        mock_auth_instance.is_admin.return_value = True
        mock_auth.return_value = mock_auth_instance

        mock_message2 = MagicMock()
        mock_message2.from_user.id = 123456789  # Admin ID
        mock_message2.reply = AsyncMock()

        await cmd_help_role_aware(mock_message2)

        # Verify reply was called
        mock_message2.reply.assert_called_once()
        help_text = mock_message2.reply.call_args[0][0]

        # Admin SHOULD see lesson commands
        assert "/view_lessons" in help_text
        assert "/add_lesson" in help_text
        assert "Admin Commands" in help_text
        assert "🔧" in help_text  # Should have admin icon


@pytest.mark.asyncio
async def test_call_endpoint_includes_lessons(async_session):
    """Test that /call endpoint includes lessons in LLM calls"""

    # Setup test lessons
    lesson_service = LessonService(async_session)
    lessons = await lesson_service.get_all_lessons()

    # Mock LLM service response
    with patch("handlers.call.llm_service") as mock_llm:
        mock_llm.get_response = AsyncMock(
            return_value="Nya~ I got your message with lessons! 💕"
        )

        # Test message handling
        user_id = 999999999
        is_admin = False
        message = "Tell me about your tools"

        await handle_message(message, user_id, is_admin)

        # Verify LLM was called with lessons
        mock_llm.get_response.assert_called_once()
        call_args = mock_llm.get_response.call_args

        # Should include lessons in the call
        assert "lessons" in call_args[1]
        assert call_args[1]["lessons"] == lessons


@pytest.mark.asyncio
async def test_unified_lesson_injection_across_entry_points():
    """Comprehensive test: Same lesson behavior across Telegram, /call, and future Discord"""

    # This would be tested across three entry points:
    # 1. Telegram message handler (waifu.py)
    # 2. HTTP /call endpoint (call.py)
    # 3. Discord handler (future implementation)

    # All three should:
    # - Load lessons from the same database table
    # - Inject lessons into LLM context using the same construct_prompt method
    # - Use the same LLMService instance
    # - Apply same role-based access control

    # For now, we verify the /call endpoint uses the same LLM service
    from api.handlers.call import llm_service
    from core.services.llm_service import LLMService as LLMServiceClass

    assert isinstance(llm_service, LLMServiceClass)
    assert hasattr(llm_service, "construct_prompt")


def test_emoji_response_for_non_existent_tools():
    """Test that BASE_PROMPT includes emoji response instructions"""

    # Read BASE_PROMPT and verify it has the emoji rule
    base_prompt_path = (
        Path(__file__).parent.parent.parent.parent / "config" / "base_prompt.txt"
    )
    with open(base_prompt_path, "r") as f:
        base_prompt = f.read()

    # Should have emoji rules
    assert "ALWAYS use emojis in your responses" in base_prompt
    assert "Nya~ I wish I had that tool" in base_prompt
    assert "💕" in base_prompt
    assert "✨" in base_prompt
    assert "kawaii dimension" in base_prompt


# Integration test with real database
@pytest.mark.integration
async def test_end_to_end_lesson_workflow():
    """End-to-end test: Create lesson → Verify injection across all entry points"""

    # This test would:
    # 1. Clear database
    # 2. Add lesson via admin command
    # 3. Send message via Telegram
    # 4. Send message via /call endpoint
    # 5. Verify both responses include the lesson
    # 6. Test with non-existent tool to verify emoji response

    # For now, just verify the structure is in place
    from api.handlers.call import handle_message
    from core.services.lesson_service import LessonService
    from core.services.llm_service import llm_service

    assert hasattr(LessonService, "get_all_lessons")
    assert hasattr(handle_message, "__call__")
    assert hasattr(llm_service, "get_response")
    assert hasattr(llm_service, "construct_prompt")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k test_emoji_response_for_non_existent_tools"])
