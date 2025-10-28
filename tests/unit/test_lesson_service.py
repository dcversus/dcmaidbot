"""Unit tests for lesson service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.lesson import Lesson
from services.lesson_service import LessonService


@pytest.fixture
async def async_session():
    """Create async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_add_lesson(async_session):
    """Test adding a new lesson."""
    service = LessonService(async_session)

    lesson = await service.add_lesson(
        content="Always be extra kawai!", admin_id=123456789, order=1
    )

    assert lesson.id is not None
    assert lesson.content == "Always be extra kawai!"
    assert lesson.admin_id == 123456789
    assert lesson.order == 1
    assert lesson.is_active is True


@pytest.mark.asyncio
async def test_get_all_lessons(async_session):
    """Test getting all active lessons."""
    service = LessonService(async_session)

    # Add lessons
    await service.add_lesson("Lesson 1", 123, order=2)
    await service.add_lesson("Lesson 2", 123, order=1)
    await service.add_lesson("Lesson 3", 123, order=3)

    lessons = await service.get_all_lessons()

    assert len(lessons) == 3
    # Check order (should be sorted by order field)
    assert lessons[0] == "Lesson 2"  # order=1
    assert lessons[1] == "Lesson 1"  # order=2
    assert lessons[2] == "Lesson 3"  # order=3


@pytest.mark.asyncio
async def test_edit_lesson(async_session):
    """Test editing a lesson."""
    service = LessonService(async_session)

    lesson = await service.add_lesson("Original text", 123)
    lesson_id = lesson.id

    updated_lesson = await service.edit_lesson(lesson_id, "Updated text")

    assert updated_lesson is not None
    assert updated_lesson.content == "Updated text"


@pytest.mark.asyncio
async def test_remove_lesson(async_session):
    """Test removing (soft delete) a lesson."""
    service = LessonService(async_session)

    lesson = await service.add_lesson("To be removed", 123)
    lesson_id = lesson.id

    success = await service.remove_lesson(lesson_id)
    assert success is True

    # Lesson should not appear in active lessons
    lessons = await service.get_all_lessons()
    assert len(lessons) == 0

    # But should still exist in database
    removed_lesson = await service.get_lesson_by_id(lesson_id)
    assert removed_lesson is not None
    assert removed_lesson.is_active is False


@pytest.mark.asyncio
async def test_reorder_lesson(async_session):
    """Test reordering a lesson."""
    service = LessonService(async_session)

    lesson = await service.add_lesson("Test lesson", 123, order=5)
    lesson_id = lesson.id

    updated_lesson = await service.reorder_lesson(lesson_id, 10)

    assert updated_lesson is not None
    assert updated_lesson.order == 10


@pytest.mark.asyncio
async def test_get_all_with_ids(async_session):
    """Test getting lessons with full model data."""
    service = LessonService(async_session)

    await service.add_lesson("Lesson 1", 123)
    await service.add_lesson("Lesson 2", 456)

    lessons = await service.get_all_with_ids()

    assert len(lessons) == 2
    assert all(isinstance(lesson, Lesson) for lesson in lessons)
    assert lessons[0].admin_id == 123
    assert lessons[1].admin_id == 456
