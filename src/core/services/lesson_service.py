"""Lesson service for CRUD operations and Redis caching."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.lesson import Lesson
from src.core.services.redis_service import redis_service


class LessonService:
    """Service for managing lessons (admin-controlled prompts)."""

    CACHE_KEY = "lessons:all"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, session: AsyncSession):
        """
        Initialize lesson service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_all_lessons(self) -> list[str]:
        """
        Get all active lessons (Redis cached).

        Returns:
            List of lesson content strings
        """
        # Try Redis cache first
        cached = await redis_service.get_json(self.CACHE_KEY)
        if cached:
            return cached

        # Fallback to PostgreSQL
        result = await self.session.execute(
            select(Lesson).where(Lesson.is_active).order_by(Lesson.order, Lesson.id)
        )
        lessons = result.scalars().all()
        lesson_texts = [lesson.content for lesson in lessons]

        # Cache in Redis
        await redis_service.set_json(self.CACHE_KEY, lesson_texts, self.CACHE_TTL)

        return lesson_texts

    async def get_all_with_ids(self) -> list[Lesson]:
        """
        Get all active lessons with full model data (admin view).

        Returns:
            List of Lesson models
        """
        result = await self.session.execute(
            select(Lesson).where(Lesson.is_active).order_by(Lesson.order, Lesson.id)
        )
        return list(result.scalars().all())

    async def add_lesson(self, content: str, admin_id: int, order: int = 0) -> Lesson:
        """
        Add new lesson (admin-only).

        Args:
            content: Lesson text/instructions
            admin_id: Telegram ID of admin creating lesson
            order: Display order (default 0)

        Returns:
            Created Lesson model
        """
        lesson = Lesson(content=content, admin_id=admin_id, order=order)
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)

        # Invalidate cache
        await redis_service.delete(self.CACHE_KEY)

        return lesson

    async def edit_lesson(self, lesson_id: int, content: str) -> Optional[Lesson]:
        """
        Edit lesson content (admin-only).

        Args:
            lesson_id: ID of lesson to edit
            content: New lesson text

        Returns:
            Updated Lesson model or None if not found
        """
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            return None

        lesson.content = content
        await self.session.commit()
        await self.session.refresh(lesson)

        # Invalidate cache
        await redis_service.delete(self.CACHE_KEY)

        return lesson

    async def reorder_lesson(self, lesson_id: int, new_order: int) -> Optional[Lesson]:
        """
        Change lesson order (admin-only).

        Args:
            lesson_id: ID of lesson to reorder
            new_order: New order value

        Returns:
            Updated Lesson model or None if not found
        """
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            return None

        lesson.order = new_order
        await self.session.commit()
        await self.session.refresh(lesson)

        # Invalidate cache
        await redis_service.delete(self.CACHE_KEY)

        return lesson

    async def remove_lesson(self, lesson_id: int) -> bool:
        """
        Remove lesson (soft delete - mark as inactive).

        Args:
            lesson_id: ID of lesson to remove

        Returns:
            True if lesson was removed, False if not found
        """
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            return False

        lesson.is_active = False
        await self.session.commit()

        # Invalidate cache
        await redis_service.delete(self.CACHE_KEY)

        return True

    async def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """
        Get lesson by ID.

        Args:
            lesson_id: ID of lesson

        Returns:
            Lesson model or None if not found
        """
        result = await self.session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        return result.scalar_one_or_none()
