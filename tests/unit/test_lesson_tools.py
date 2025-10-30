"""Unit tests for lesson tools and tool executor with role-based access."""

import pytest
from unittest.mock import patch

from tools.tool_executor import ToolExecutor
from tools.lesson_tools import LESSON_TOOLS


# Test tool definitions
def test_lesson_tools_definitions():
    """Test that all lesson tools are defined correctly."""
    assert len(LESSON_TOOLS) == 4

    tool_names = [tool["function"]["name"] for tool in LESSON_TOOLS]
    assert "get_all_lessons" in tool_names
    assert "create_lesson" in tool_names
    assert "edit_lesson" in tool_names
    assert "delete_lesson" in tool_names


def test_get_all_lessons_tool_structure():
    """Test get_all_lessons tool definition structure."""
    tool = next(t for t in LESSON_TOOLS if t["function"]["name"] == "get_all_lessons")

    assert tool["type"] == "function"
    assert "ADMIN ONLY" in tool["function"]["description"]
    assert "parameters" in tool["function"]
    assert tool["function"]["parameters"]["type"] == "object"


def test_create_lesson_tool_structure():
    """Test create_lesson tool definition structure."""
    tool = next(t for t in LESSON_TOOLS if t["function"]["name"] == "create_lesson")

    assert tool["type"] == "function"
    assert "ADMIN ONLY" in tool["function"]["description"]

    params = tool["function"]["parameters"]["properties"]
    assert "content" in params
    assert "order" in params
    assert "content" in tool["function"]["parameters"]["required"]


def test_edit_lesson_tool_structure():
    """Test edit_lesson tool definition structure."""
    tool = next(t for t in LESSON_TOOLS if t["function"]["name"] == "edit_lesson")

    assert tool["type"] == "function"
    assert "ADMIN ONLY" in tool["function"]["description"]

    params = tool["function"]["parameters"]["properties"]
    assert "lesson_id" in params
    assert "content" in params
    assert set(tool["function"]["parameters"]["required"]) == {"lesson_id", "content"}


def test_delete_lesson_tool_structure():
    """Test delete_lesson tool definition structure."""
    tool = next(t for t in LESSON_TOOLS if t["function"]["name"] == "delete_lesson")

    assert tool["type"] == "function"
    assert "ADMIN ONLY" in tool["function"]["description"]

    params = tool["function"]["parameters"]["properties"]
    assert "lesson_id" in params
    assert "lesson_id" in tool["function"]["parameters"]["required"]


# Test tool executor with role-based access
@pytest.mark.asyncio
async def test_admin_can_get_all_lessons(async_session):
    """Test that admin can successfully call get_all_lessons."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        # Add a lesson first
        from services.lesson_service import LessonService

        lesson_service = LessonService(async_session)
        await lesson_service.add_lesson("Test lesson", 123)

        result = await executor.execute(
            tool_name="get_all_lessons", arguments={}, user_id=123
        )

        assert result["success"] is True
        assert "lessons" in result
        assert result["count"] == 1


@pytest.mark.asyncio
async def test_non_admin_cannot_get_all_lessons(async_session):
    """Test that non-admin gets access denied for get_all_lessons."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="get_all_lessons", arguments={}, user_id=999
        )

        assert result["success"] is False
        assert result["error"] == "access_denied"
        assert "vague_message" in result
        # Vague message should be present and non-empty (randomized)
        assert len(result["vague_message"]) > 0


@pytest.mark.asyncio
async def test_admin_can_create_lesson(async_session):
    """Test that admin can successfully create a lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="create_lesson",
            arguments={"content": "Always be kawaii!", "order": 5},
            user_id=123,
        )

        assert result["success"] is True
        assert result["lesson_id"] is not None
        assert "created successfully" in result["message"]


@pytest.mark.asyncio
async def test_non_admin_cannot_create_lesson(async_session):
    """Test that non-admin gets access denied for create_lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="create_lesson",
            arguments={"content": "Evil lesson"},
            user_id=999,
        )

        assert result["success"] is False
        assert result["error"] == "access_denied"
        assert "vague_message" in result


@pytest.mark.asyncio
async def test_admin_can_edit_lesson(async_session):
    """Test that admin can successfully edit a lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        # Create a lesson first
        from services.lesson_service import LessonService

        lesson_service = LessonService(async_session)
        lesson = await lesson_service.add_lesson("Original", 123)

        executor = ToolExecutor(async_session)
        result = await executor.execute(
            tool_name="edit_lesson",
            arguments={"lesson_id": lesson.id, "content": "Updated"},
            user_id=123,
        )

        assert result["success"] is True
        assert result["lesson"]["content"] == "Updated"


@pytest.mark.asyncio
async def test_non_admin_cannot_edit_lesson(async_session):
    """Test that non-admin gets access denied for edit_lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="edit_lesson",
            arguments={"lesson_id": 1, "content": "Hacked"},
            user_id=999,
        )

        assert result["success"] is False
        assert result["error"] == "access_denied"


@pytest.mark.asyncio
async def test_admin_can_delete_lesson(async_session):
    """Test that admin can successfully delete a lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        # Create a lesson first
        from services.lesson_service import LessonService

        lesson_service = LessonService(async_session)
        lesson = await lesson_service.add_lesson("To delete", 123)

        executor = ToolExecutor(async_session)
        result = await executor.execute(
            tool_name="delete_lesson",
            arguments={"lesson_id": lesson.id},
            user_id=123,
        )

        assert result["success"] is True
        assert "deleted successfully" in result["message"]


@pytest.mark.asyncio
async def test_non_admin_cannot_delete_lesson(async_session):
    """Test that non-admin gets access denied for delete_lesson."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="delete_lesson",
            arguments={"lesson_id": 1},
            user_id=999,
        )

        assert result["success"] is False
        assert result["error"] == "access_denied"


@pytest.mark.asyncio
async def test_create_lesson_missing_content(async_session):
    """Test that create_lesson fails without content."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="create_lesson",
            arguments={},  # Missing content
            user_id=123,
        )

        assert result["success"] is False
        assert "content is required" in result["error"].lower()


@pytest.mark.asyncio
async def test_edit_lesson_not_found(async_session):
    """Test that editing non-existent lesson returns error."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="edit_lesson",
            arguments={"lesson_id": 99999, "content": "Updated"},
            user_id=123,
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_delete_lesson_not_found(async_session):
    """Test that deleting non-existent lesson returns error."""
    with (
        patch.dict("os.environ", {"ADMIN_IDS": "123"}),
        patch("tools.tool_executor.LLMService"),
    ):
        executor = ToolExecutor(async_session)

        result = await executor.execute(
            tool_name="delete_lesson",
            arguments={"lesson_id": 99999},
            user_id=123,
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()
