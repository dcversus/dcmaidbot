"""E2E test for LLM integration with lessons."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.llm_service import LLMService
from services.lesson_service import LessonService

# async_session fixture is provided by tests/conftest.py (PostgreSQL)


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("services.llm_service.AsyncOpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_llm_with_lessons_e2e(async_session, mock_openai):
    """
    E2E test: Add lessons to database, get LLM response with lessons injected.
    """
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Nya! I'm following my secret lessons! 💕"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create lesson service and add lessons
    lesson_service = LessonService(async_session)
    await lesson_service.add_lesson("Always say nya!", 123, order=1)
    await lesson_service.add_lesson("Be extra kawai with coding topics", 123, order=2)

    # Get lessons
    lessons = await lesson_service.get_all_lessons()
    assert len(lessons) == 2
    assert lessons[0] == "Always say nya!"
    assert lessons[1] == "Be extra kawai with coding topics"

    # Create LLM service and get response
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    user_info = {"username": "testuser", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}

    response = await llm_service.get_response(
        user_message="Tell me about Python!",
        user_info=user_info,
        chat_info=chat_info,
        lessons=lessons,
    )

    # Verify response
    assert response == "Nya! I'm following my secret lessons! 💕"

    # Verify API was called with lessons in prompt
    call_args = mock_openai.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]

    assert "Always say nya!" in system_prompt
    assert "Be extra kawai with coding topics" in system_prompt
    assert "LESSONS" in system_prompt
    assert "SECRET" in system_prompt


@pytest.mark.asyncio
async def test_llm_admin_only_behavior(async_session, mock_openai):
    """
    E2E test: Verify lessons are properly loaded and used in context.
    """
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Hello admin! 💕"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    # Add admin-specific lesson
    lesson_service = LessonService(async_session)
    await lesson_service.add_lesson(
        "Always greet admins with extra love!", admin_id=123456789
    )

    lessons = await lesson_service.get_all_lessons()

    # Get LLM response for admin
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm_service = LLMService()
        llm_service.client = mock_openai

    user_info = {"username": "admin", "telegram_id": 123456789}
    chat_info = {"type": "private", "chat_id": 123456789}

    response = await llm_service.get_response(
        user_message="Hello!", user_info=user_info, chat_info=chat_info, lessons=lessons
    )

    assert response == "Hello admin! 💕"

    # Verify lesson in context
    call_args = mock_openai.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]

    assert "Always greet admins with extra love!" in system_prompt
