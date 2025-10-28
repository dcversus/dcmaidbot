"""Unit tests for LLM service."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.llm_service import LLMService


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("services.llm_service.AsyncOpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_load_base_prompt():
    """Test loading BASE_PROMPT from config file."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()
        assert service.base_prompt is not None
        assert "DCMaid" in service.base_prompt
        assert "kawai" in service.base_prompt


def test_construct_prompt():
    """Test prompt construction with BASE_PROMPT and LESSONS."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()

    user_info = {"username": "testuser", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}
    lessons = ["Always be polite", "Respond with enthusiasm"]

    prompt = service.construct_prompt(
        user_message="Hello!", user_info=user_info, chat_info=chat_info, lessons=lessons
    )

    assert "DCMaid" in prompt
    assert "testuser" in prompt
    assert "123" in prompt
    assert "Always be polite" in prompt
    assert "Respond with enthusiasm" in prompt
    assert "LESSONS" in prompt
    assert "SECRET" in prompt


def test_construct_prompt_no_lessons():
    """Test prompt construction with no lessons."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()

    user_info = {"username": "testuser", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}

    prompt = service.construct_prompt(
        user_message="Hello!", user_info=user_info, chat_info=chat_info, lessons=[]
    )

    assert "DCMaid" in prompt
    assert "No lessons configured yet" in prompt


@pytest.mark.asyncio
async def test_get_response_success(mock_openai):
    """Test successful LLM response."""
    # Mock API response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Nya! Hello there! 💕"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()
        service.client = mock_openai

    user_info = {"username": "test", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}

    response = await service.get_response(
        user_message="Hello!",
        user_info=user_info,
        chat_info=chat_info,
        lessons=["Be kawai"],
    )

    assert response == "Nya! Hello there! 💕"
    assert mock_openai.chat.completions.create.called


@pytest.mark.asyncio
async def test_get_response_api_error(mock_openai):
    """Test LLM response when API fails."""
    mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()
        service.client = mock_openai

    user_info = {"username": "test", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}

    response = await service.get_response(
        user_message="Hello!", user_info=user_info, chat_info=chat_info, lessons=[]
    )

    assert "went wrong" in response


@pytest.mark.asyncio
async def test_get_response_with_tools(mock_openai):
    """Test LLM response with tool schemas."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Using tools!"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()
        service.client = mock_openai

    user_info = {"username": "test", "telegram_id": 123}
    chat_info = {"type": "private", "chat_id": 123}
    tools = [{"type": "function", "function": {"name": "test_tool"}}]

    response = await service.get_response(
        user_message="Use a tool!",
        user_info=user_info,
        chat_info=chat_info,
        lessons=[],
        tools=tools,
    )

    assert response == "Using tools!"
    call_args = mock_openai.chat.completions.create.call_args
    assert "tools" in call_args.kwargs
    assert call_args.kwargs["tools"] == tools


def test_reload_base_prompt():
    """Test reloading BASE_PROMPT."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        service = LLMService()
        original_prompt = service.base_prompt

        service.reload_base_prompt()

        assert service.base_prompt == original_prompt
