"""Enhanced Memory model with VAD emotions and Zettelkasten attributes (PRP-005).

This implementation is based on cutting-edge research:
- A-MEM (NeurIPS 2025): Zettelkasten-inspired agentic memory
- VAD Model: Valence-Arousal-Dominance emotional dimensions
- Knowledge Graphs: Graph-based memory organization
- Social Graph AI: Relationship and personality modeling
"""

import json
import os
from datetime import datetime
from typing import Any, Optional, cast

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.services.database import Base

# Import pgvector for vector embeddings
try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback for environments without pgvector
    PGVECTOR_AVAILABLE = False
    Vector = None

# Detect database type from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dcmaidbot_test.db")
IS_SQLITE = "sqlite" in DATABASE_URL.lower()


# Association table for Memory <-> Category many-to-many relationship
memory_category_association = Table(
    "memory_category_association",
    Base.metadata,
    Column(
        "memory_id",
        Integer,
        ForeignKey("memories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    extend_existing=True,
)


class Memory(Base):
    """Enhanced Memory with VAD emotions and Zettelkasten attributes.

    Based on A-MEM (NeurIPS 2025) and VAD emotion model research.
    Supports dynamic linking, emotional context, and memory evolution.
    """

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Content (A-MEM inspired)
    simple_content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # ~500 tokens: emotions + key facts + relationships
    full_content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # ~4000 tokens: detailed information with full context
    importance: Mapped[int] = mapped_column(Integer, default=0, index=True)  # 0-9999+

    # Emotional Context (VAD Model: Mehrabian & Russell, 1974)
    emotion_valence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # -1.0 (negative) to +1.0 (positive)
    emotion_arousal: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # -1.0 (calm) to +1.0 (excited)
    emotion_dominance: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # -1.0 (submissive) to +1.0 (dominant)
    emotion_label: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # "joy", "sadness", "anger", etc.

    # Zettelkasten Attributes (for dynamic linking and organization)
    # Use Text for SQLite, ARRAY for PostgreSQL
    _keywords_storage: Mapped[Optional[Any]] = mapped_column(
        "keywords", Text if IS_SQLITE else ARRAY(String), nullable=True
    )
    _tags_storage: Mapped[Optional[Any]] = mapped_column(
        "tags", Text if IS_SQLITE else ARRAY(String), nullable=True
    )
    context_temporal: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # When this happened
    context_situational: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Situation/setting

    # Versioning & Evolution (A-MEM memory evolution)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("memories.id"), nullable=True
    )
    _evolution_triggers_storage: Mapped[Optional[Any]] = mapped_column(
        "evolution_triggers", Text if IS_SQLITE else ARRAY(Integer), nullable=True
    )

    # Metadata
    created_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )  # Telegram user ID
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    # Vector embedding for semantic search (PRP-007)
    # Always use Text column to avoid database compatibility issues
    # Vector data is stored as JSON string and converted to vectors in code
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    categories: Mapped[list["Category"]] = relationship(
        secondary=memory_category_association, back_populates="memories"
    )

    parent: Mapped[Optional["Memory"]] = relationship(
        "Memory", remote_side=[id], foreign_keys=[parent_id], back_populates="versions"
    )
    versions: Mapped[list["Memory"]] = relationship(
        "Memory", back_populates="parent", cascade="all, delete-orphan"
    )

    # Zettelkasten links (bidirectional)
    outgoing_links: Mapped[list["MemoryLink"]] = relationship(
        "MemoryLink",
        foreign_keys="MemoryLink.from_memory_id",
        back_populates="from_memory",
        cascade="all, delete-orphan",
    )
    incoming_links: Mapped[list["MemoryLink"]] = relationship(
        "MemoryLink",
        foreign_keys="MemoryLink.to_memory_id",
        back_populates="to_memory",
    )

    # Property accessors for array fields (handle JSON in SQLite)
    @property
    def keywords(self) -> Optional[list[str]]:
        """Get keywords list."""
        if IS_SQLITE and isinstance(self._keywords_storage, str):
            return cast(list[str], json.loads(self._keywords_storage))
        return cast(Optional[list[str]], self._keywords_storage)

    @keywords.setter
    def keywords(self, value: Optional[list[str]]) -> None:
        """Set keywords list."""
        if IS_SQLITE and value is not None:
            self._keywords_storage = cast(Any, json.dumps(value))
        else:
            self._keywords_storage = cast(Any, value)

    @property
    def tags(self) -> Optional[list[str]]:
        """Get tags list."""
        if IS_SQLITE and isinstance(self._tags_storage, str):
            return cast(list[str], json.loads(self._tags_storage))
        return cast(Optional[list[str]], self._tags_storage)

    @tags.setter
    def tags(self, value: Optional[list[str]]) -> None:
        """Set tags list."""
        if IS_SQLITE and value is not None:
            self._tags_storage = cast(Any, json.dumps(value))
        else:
            self._tags_storage = cast(Any, value)

    @property
    def evolution_triggers(self) -> Optional[list[int]]:
        """Get evolution triggers list."""
        if IS_SQLITE and isinstance(self._evolution_triggers_storage, str):
            return cast(list[int], json.loads(self._evolution_triggers_storage))
        return cast(Optional[list[int]], self._evolution_triggers_storage)

    @evolution_triggers.setter
    def evolution_triggers(self, value: Optional[list[int]]) -> None:
        """Set evolution triggers list."""
        if IS_SQLITE and value is not None:
            self._evolution_triggers_storage = cast(Any, json.dumps(value))
        else:
            self._evolution_triggers_storage = cast(Any, value)

    def __repr__(self) -> str:
        cats = [c.name for c in self.categories] if self.categories else []
        emotion = f"{self.emotion_label}" if self.emotion_label else "neutral"
        return (
            f"<Memory(id={self.id}, importance={self.importance}, "
            f"emotion={emotion}, categories={cats})>"
        )


class Category(Base):
    """Domain-based category for organizing memories.

    Supports six top-level domains based on user research:
    1. self - Bot's identity, history, personality
    2. social - People, relationships, interactions
    3. knowledge - Technical expertise, projects
    4. interest - Tastes, preferences, humor
    5. episode - Significant events, patterns
    6. meta - Learning, reflection, evolution
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Category identification
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # self, social, knowledge, interest, episode, meta
    full_path: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )  # e.g., "social.person"

    # Category metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Emoji
    importance_range_min: Mapped[int] = mapped_column(Integer, default=0)
    importance_range_max: Mapped[int] = mapped_column(Integer, default=10000)

    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )

    # Relationships
    memories: Mapped[list["Memory"]] = relationship(
        secondary=memory_category_association, back_populates="categories"
    )
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], foreign_keys=[parent_id]
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, path={self.full_path}, icon={self.icon})>"


class MemoryLink(Base):
    """Zettelkasten-style bidirectional link between memories.

    Inspired by A-MEM (NeurIPS 2025) for dynamic memory evolution.
    Enables interconnected knowledge networks like human Zettelkasten.
    """

    __tablename__ = "memory_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Link endpoints
    from_memory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memories.id"), nullable=False, index=True
    )
    to_memory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memories.id"), nullable=False, index=True
    )

    # Link metadata
    link_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "related", "causes", "contradicts", "elaborates", "precedes", "follows"
    strength: Mapped[float] = mapped_column(
        Float, default=1.0
    )  # 0.0-1.0 (how strong is the connection)
    context: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Why this link exists

    # Lifecycle
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )  # User who created this link (PRP-006)
    auto_generated: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # LLM-generated vs manual

    # Relations
    from_memory: Mapped["Memory"] = relationship(
        "Memory",
        foreign_keys=[from_memory_id],
        back_populates="outgoing_links",
    )
    to_memory: Mapped["Memory"] = relationship(
        "Memory",
        foreign_keys=[to_memory_id],
        back_populates="incoming_links",
    )

    __table_args__ = (
        UniqueConstraint(
            "from_memory_id",
            "to_memory_id",
            "link_type",
            name="unique_memory_link",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryLink(from={self.from_memory_id}, to={self.to_memory_id}, "
            f"type={self.link_type}, strength={self.strength})>"
        )
