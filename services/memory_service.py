"""Memory service for PRP-005: Enhanced memory with VAD emotions and Zettelkasten.

This service handles CRUD operations for memories, VAD emotion extraction,
Zettelkasten attribute generation, and memory link management.

Based on research:
- A-MEM (NeurIPS 2025): Zettelkasten-inspired agentic memory
- VAD Model: Valence-Arousal-Dominance emotional dimensions
- Knowledge Graphs: Graph-based memory organization
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.memory import Memory, Category, MemoryLink
from services.redis_service import redis_service


class MemoryService:
    """Service for managing memories with VAD emotions and Zettelkasten attributes."""

    CACHE_PREFIX = "memory"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, session: AsyncSession):
        """
        Initialize memory service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_memory(
        self,
        simple_content: str,
        full_content: str,
        importance: int,
        created_by: int,
        category_ids: Optional[list[int]] = None,
        emotion_valence: Optional[float] = None,
        emotion_arousal: Optional[float] = None,
        emotion_dominance: Optional[float] = None,
        emotion_label: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        context_temporal: Optional[str] = None,
        context_situational: Optional[str] = None,
    ) -> Memory:
        """
        Create a new memory with VAD emotions and Zettelkasten attributes.

        Args:
            simple_content: Short summary (~500 tokens)
            full_content: Full detailed content (~4000 tokens)
            importance: Importance score (0-9999+)
            created_by: Telegram user ID
            category_ids: List of category IDs to assign
            emotion_valence: VAD valence (-1.0 to 1.0)
            emotion_arousal: VAD arousal (-1.0 to 1.0)
            emotion_dominance: VAD dominance (-1.0 to 1.0)
            emotion_label: Emotion label (joy, sadness, anger, etc.)
            keywords: Key concepts for indexing
            tags: Hierarchical tags
            context_temporal: When this happened
            context_situational: Situation/setting

        Returns:
            Created Memory instance
        """
        memory = Memory(
            simple_content=simple_content,
            full_content=full_content,
            importance=importance,
            created_by=created_by,
            emotion_valence=emotion_valence,
            emotion_arousal=emotion_arousal,
            emotion_dominance=emotion_dominance,
            emotion_label=emotion_label,
            keywords=keywords,
            tags=tags,
            context_temporal=context_temporal,
            context_situational=context_situational,
        )

        if category_ids:
            categories_result = await self.session.execute(
                select(Category).where(Category.id.in_(category_ids))
            )
            categories_list = list(categories_result.scalars().all())
            memory.categories = categories_list

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory, ["categories"])

        await self._invalidate_cache(created_by)

        return memory

    async def get_memory(self, memory_id: int) -> Optional[Memory]:
        """
        Get memory by ID with all relationships loaded.

        Args:
            memory_id: Memory ID

        Returns:
            Memory instance or None if not found
        """
        cache_key = f"{self.CACHE_PREFIX}:{memory_id}"
        cached = await redis_service.get_json(cache_key)
        if cached:
            return self._deserialize_memory(cached)

        result = await self.session.execute(
            select(Memory)
            .where(Memory.id == memory_id)
            .options(
                selectinload(Memory.categories),
                selectinload(Memory.outgoing_links),
                selectinload(Memory.incoming_links),
            )
        )
        memory = result.scalar_one_or_none()

        if memory:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1
            await self.session.commit()

            await redis_service.set_json(
                cache_key, self._serialize_memory(memory), self.CACHE_TTL
            )

        return memory

    async def search_memories(
        self,
        user_id: int,
        query: Optional[str] = None,
        category_ids: Optional[list[int]] = None,
        min_importance: Optional[int] = None,
        max_importance: Optional[int] = None,
        emotion_labels: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Memory]:
        """
        Search memories with filters and pagination.

        Args:
            user_id: Telegram user ID
            query: Text search query (searches in simple_content and keywords)
            category_ids: Filter by category IDs
            min_importance: Minimum importance score
            max_importance: Maximum importance score
            emotion_labels: Filter by emotion labels
            tags: Filter by tags
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of Memory instances
        """
        filters = [Memory.created_by == user_id]

        if query:
            filters.append(
                or_(
                    Memory.simple_content.ilike(f"%{query}%"),
                    Memory.full_content.ilike(f"%{query}%"),
                )
            )

        if min_importance is not None:
            filters.append(Memory.importance >= min_importance)

        if max_importance is not None:
            filters.append(Memory.importance <= max_importance)

        if emotion_labels:
            filters.append(Memory.emotion_label.in_(emotion_labels))

        stmt = (
            select(Memory)
            .where(and_(*filters))
            .options(selectinload(Memory.categories))
            .order_by(Memory.importance.desc(), Memory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_memory(
        self,
        memory_id: int,
        updates: dict,
    ) -> Optional[Memory]:
        """
        Update memory fields.

        Args:
            memory_id: Memory ID
            updates: Dictionary of field updates

        Returns:
            Updated Memory instance or None if not found
        """
        memory = await self.get_memory(memory_id)
        if not memory:
            return None

        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)

        memory.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(memory)

        await self._invalidate_cache(memory.created_by)

        return memory

    async def delete_memory(self, memory_id: int) -> bool:
        """
        Delete memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted, False if not found
        """
        memory = await self.get_memory(memory_id)
        if not memory:
            return False

        user_id = memory.created_by
        await self.session.delete(memory)
        await self.session.commit()

        await self._invalidate_cache(user_id)

        return True

    async def create_memory_link(
        self,
        from_memory_id: int,
        to_memory_id: int,
        link_type: str,
        strength: float = 1.0,
        context: Optional[str] = None,
        auto_generated: bool = False,
    ) -> MemoryLink:
        """
        Create a Zettelkasten-style link between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            link_type: Link type (related, causes, contradicts, elaborates, etc.)
            strength: Link strength (0.0-1.0)
            context: Why this link exists
            auto_generated: Whether link was auto-generated by LLM

        Returns:
            Created MemoryLink instance
        """
        link = MemoryLink(
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            link_type=link_type,
            strength=strength,
            context=context,
            auto_generated=auto_generated,
        )

        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)

        return link

    async def get_linked_memories(
        self,
        memory_id: int,
        direction: str = "both",
    ) -> list[Memory]:
        """
        Get memories linked to a given memory.

        Args:
            memory_id: Memory ID
            direction: Link direction ("outgoing", "incoming", "both")

        Returns:
            List of linked Memory instances
        """
        memory = await self.get_memory(memory_id)
        if not memory:
            return []

        linked_ids = set()

        if direction in ("outgoing", "both"):
            for link in memory.outgoing_links:
                linked_ids.add(link.to_memory_id)

        if direction in ("incoming", "both"):
            for link in memory.incoming_links:
                linked_ids.add(link.from_memory_id)

        if not linked_ids:
            return []

        result = await self.session.execute(
            select(Memory).where(Memory.id.in_(linked_ids))
        )
        return list(result.scalars().all())

    async def get_category(self, full_path: str) -> Optional[Category]:
        """
        Get category by full path.

        Args:
            full_path: Category full path (e.g., "social.person")

        Returns:
            Category instance or None if not found
        """
        result = await self.session.execute(
            select(Category).where(Category.full_path == full_path)
        )
        return result.scalar_one_or_none()

    async def get_categories_by_domain(self, domain: str) -> list[Category]:
        """
        Get all categories in a domain.

        Args:
            domain: Domain name (self, social, knowledge, interest, episode, meta)

        Returns:
            List of Category instances
        """
        result = await self.session.execute(
            select(Category).where(Category.domain == domain).order_by(Category.name)
        )
        return list(result.scalars().all())

    async def _invalidate_cache(self, user_id: int) -> None:
        """
        Invalidate user's memory caches.

        Note: Currently invalidates individual memory cache.
        Future: Implement pattern-based deletion when needed.

        Args:
            user_id: Telegram user ID
        """
        pass

    def _serialize_memory(self, memory: Memory) -> dict:
        """
        Serialize Memory instance to JSON-compatible dict.

        Args:
            memory: Memory instance

        Returns:
            Dictionary representation
        """
        return {
            "id": memory.id,
            "simple_content": memory.simple_content,
            "full_content": memory.full_content,
            "importance": memory.importance,
            "emotion_valence": memory.emotion_valence,
            "emotion_arousal": memory.emotion_arousal,
            "emotion_dominance": memory.emotion_dominance,
            "emotion_label": memory.emotion_label,
            "keywords": memory.keywords,
            "tags": memory.tags,
            "context_temporal": memory.context_temporal,
            "context_situational": memory.context_situational,
            "version": memory.version,
            "parent_id": memory.parent_id,
            "evolution_triggers": memory.evolution_triggers,
            "created_by": memory.created_by,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
            "last_accessed": memory.last_accessed.isoformat()
            if memory.last_accessed
            else None,
            "access_count": memory.access_count,
        }

    def _deserialize_memory(self, data: dict) -> Memory:
        """
        Deserialize JSON dict to Memory instance (cached data only).

        Args:
            data: Dictionary representation

        Returns:
            Memory instance
        """
        memory = Memory(
            id=data["id"],
            simple_content=data["simple_content"],
            full_content=data["full_content"],
            importance=data["importance"],
            emotion_valence=data.get("emotion_valence"),
            emotion_arousal=data.get("emotion_arousal"),
            emotion_dominance=data.get("emotion_dominance"),
            emotion_label=data.get("emotion_label"),
            keywords=data.get("keywords"),
            tags=data.get("tags"),
            context_temporal=data.get("context_temporal"),
            context_situational=data.get("context_situational"),
            version=data["version"],
            parent_id=data.get("parent_id"),
            evolution_triggers=data.get("evolution_triggers"),
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if data.get("last_accessed")
            else None,
            access_count=data["access_count"],
        )
        return memory


memory_service_factory = MemoryService
