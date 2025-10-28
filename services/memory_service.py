"""Memory Service for PRP-005: Advanced Memory System.

Provides CRUD operations for memories with:
- LLM-generated simple content extraction
- Automatic importance scoring
- Category management
- Redis caching
- Access tracking
"""

import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.memory import Memory, Category
from services.llm_service import LLMService
from services.redis_service import redis_service


class MemoryService:
    """Service for managing memories with LLM integration and caching."""

    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize Memory Service.

        Args:
            llm_service: Optional LLM service instance for content processing
        """
        self.llm_service = llm_service or LLMService()

    async def create_memory(
        self,
        session: AsyncSession,
        full_content: str,
        categories: list[str],
        created_by: int,
        importance: Optional[int] = None,
    ) -> Memory:
        """Create new memory with LLM-generated simple content and importance.

        Args:
            session: Database session
            full_content: Full detailed content (~4000 tokens)
            categories: List of category names
            created_by: User ID creating the memory
            importance: Optional manual importance score (0-9999+)

        Returns:
            Created Memory instance
        """

        # Generate simple content using LLM
        simple_content = await self._extract_simple_content(full_content)

        # Calculate importance if not provided
        if importance is None:
            importance = await self._calculate_importance(full_content)

        # Create memory
        memory = Memory(
            simple_content=simple_content,
            full_content=full_content,
            importance=importance,
            created_by=created_by,
        )

        # Add categories
        for cat_name in categories:
            category = await self._get_or_create_category(session, cat_name)
            memory.categories.append(category)

        session.add(memory)
        await session.flush()
        await session.refresh(memory)

        # Cache in Redis
        await self._cache_memory(memory)

        return memory

    async def get_memory(
        self, session: AsyncSession, memory_id: int, full: bool = False
    ) -> dict:
        """Get memory by ID. Returns simple or full content.

        Args:
            session: Database session
            memory_id: Memory ID to retrieve
            full: Whether to retrieve full content (True) or simple summary (False)

        Returns:
            dict: Memory data with content, importance, categories, etc.
        """

        # Try Redis cache first
        cache_key = f"memory:{memory_id}:{'full' if full else 'simple'}"
        cached = await redis_service.get(cache_key)
        if cached:
            return json.loads(cached)

        # Get from database
        result = await session.execute(select(Memory).where(Memory.id == memory_id))
        memory = result.scalar_one()

        # Update access tracking
        memory.last_accessed = datetime.now(timezone.utc)
        memory.access_count += 1
        await session.flush()

        # Prepare response
        result_dict = {
            "id": memory.id,
            "content": memory.full_content if full else memory.simple_content,
            "importance": memory.importance,
            "categories": [c.name for c in memory.categories],
            "version": memory.version,
            "created_by": memory.created_by,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "access_count": memory.access_count,
        }

        # Cache result (TTL: 3600s for simple, 1800s for full)
        ttl = 1800 if full else 3600
        await redis_service.setex(cache_key, ttl, json.dumps(result_dict))

        return result_dict

    async def search_memories(
        self,
        session: AsyncSession,
        query: Optional[str] = None,
        categories: Optional[list[str]] = None,
        min_importance: int = 0,
        limit: int = 10,
    ) -> list[dict]:
        """Search memories with filters.

        Args:
            session: Database session
            query: Optional text query (not implemented yet - Phase 2+)
            categories: Filter by category names
            min_importance: Minimum importance score
            limit: Maximum number of results

        Returns:
            list[dict]: List of matching memories
        """

        stmt = select(Memory)

        # Filter by categories
        if categories:
            stmt = (
                stmt.join(Memory.categories)
                .where(Category.name.in_(categories))
                .distinct()
            )

        # Filter by importance
        stmt = stmt.where(Memory.importance >= min_importance)

        # Order by importance (highest first)
        stmt = stmt.order_by(Memory.importance.desc()).limit(limit)

        result = await session.execute(stmt)
        memories = result.scalars().all()

        return [
            {
                "id": m.id,
                "simple_content": m.simple_content,
                "importance": m.importance,
                "categories": [c.name for c in m.categories],
                "access_count": m.access_count,
            }
            for m in memories
        ]

    async def update_memory(
        self, session: AsyncSession, memory_id: int, full_content: str
    ) -> Memory:
        """Update memory with new content (creates new version).

        Args:
            session: Database session
            memory_id: Memory ID to update
            full_content: New full content

        Returns:
            Updated Memory instance
        """

        result = await session.execute(select(Memory).where(Memory.id == memory_id))
        original = result.scalar_one()

        # Generate new simple content
        simple_content = await self._extract_simple_content(full_content)

        # Recalculate importance
        importance = await self._calculate_importance(full_content)

        # Update memory
        original.simple_content = simple_content
        original.full_content = full_content
        original.importance = importance
        original.version += 1
        original.updated_at = datetime.now(timezone.utc)

        await session.flush()

        # Invalidate cache
        await redis_service.delete(f"memory:{memory_id}:simple")
        await redis_service.delete(f"memory:{memory_id}:full")

        return original

    async def delete_memory(self, session: AsyncSession, memory_id: int) -> bool:
        """Delete memory by ID.

        Args:
            session: Database session
            memory_id: Memory ID to delete

        Returns:
            bool: True if deleted, False if not found
        """

        result = await session.execute(select(Memory).where(Memory.id == memory_id))
        memory = result.scalar_one_or_none()

        if not memory:
            return False

        await session.delete(memory)
        await session.flush()

        # Invalidate cache
        await redis_service.delete(f"memory:{memory_id}:simple")
        await redis_service.delete(f"memory:{memory_id}:full")

        return True

    # Private helper methods

    async def _extract_simple_content(self, full_content: str) -> str:
        """Extract simple content (~500 tokens) from full content using LLM.

        Args:
            full_content: Full detailed content

        Returns:
            Simple summary focusing on emotions and key facts
        """

        prompt = f"""Given this detailed memory, extract the most important \
information focusing on EMOTIONAL SIGNALS and KEY FACTS. \
Keep it under 500 tokens (~2000 characters).

Full Memory:
{full_content}

Extract:
1. Core emotional signals (happiness, sadness, anxiety, etc.)
2. Key facts that define this memory
3. Most important relationships or connections
4. Critical details that MUST be remembered

Format as a concise summary focusing on emotions and key facts."""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3,
            )
            return response.choices[0].message.content or full_content[:2000]
        except Exception as e:
            print(f"⚠️  LLM extraction failed: {e}")
            # Fallback: truncate full content
            return full_content[:2000]

    async def _calculate_importance(self, content: str) -> int:
        """Calculate importance score (0-9999+) for memory using LLM.

        Args:
            content: Memory content

        Returns:
            Importance score (0-9999+)
        """

        prompt = f"""Rate the importance of this memory on a scale from 0 \
(useless/trivial) to 9999+ (CRITICAL/life-changing).

Memory:
{content}

Scoring Guide:
0-10: Trivial information (weather, random facts)
11-100: Casual information (preferences, minor events)
101-500: Notable information (interests, friends)
501-1000: Important information (significant events, close relationships)
1001-5000: Very important (major life events, deep relationships)
5001-9999: Critical (life-changing events, core relationships)
10000+: MAXIMUM IMPORTANCE (admins, core identity)

Return only the numeric score."""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0,
            )
            return int(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"⚠️  LLM importance calculation failed: {e}")
            # Default to moderate importance
            return 100

    async def _get_or_create_category(
        self, session: AsyncSession, name: str
    ) -> Category:
        """Get existing category or create new one.

        Args:
            session: Database session
            name: Category name

        Returns:
            Category instance
        """

        # Try to find existing category
        result = await session.execute(select(Category).where(Category.name == name))
        category = result.scalar_one_or_none()

        if category:
            return category

        # Create new category
        category = Category(name=name, description=f"User-defined category: {name}")
        session.add(category)
        await session.flush()

        return category

    async def _cache_memory(self, memory: Memory) -> None:
        """Cache memory in Redis for fast access.

        Args:
            memory: Memory instance to cache
        """

        # Cache simple content (TTL: 3600s)
        simple_data = {
            "id": memory.id,
            "content": memory.simple_content,
            "importance": memory.importance,
            "categories": [c.name for c in memory.categories],
            "version": memory.version,
        }
        await redis_service.setex(
            f"memory:{memory.id}:simple", 3600, json.dumps(simple_data)
        )

        # Cache full content (TTL: 1800s - less frequently accessed)
        full_data = {
            **simple_data,
            "content": memory.full_content,
        }
        await redis_service.setex(
            f"memory:{memory.id}:full", 1800, json.dumps(full_data)
        )


# Singleton instance
memory_service = MemoryService()
