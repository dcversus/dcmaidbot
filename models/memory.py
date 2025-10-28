"""Memory model for PRP-005: Advanced Memory System."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Integer,
    Text,
    DateTime,
    Table,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


# Association table for many-to-many relationship between memories and categories
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
)


class Memory(Base):
    """Memory model - Knowledge graph with simple/full content forms.

    PRP-005: Basic Memory System
    - Two content forms (simple ~500 tokens, full ~4000 tokens)
    - Importance scoring (0-9999+)
    - Categories for organization
    - Version tracking
    - Access tracking for optimization
    """

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Content forms
    simple_content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="~500 tokens - emotional signals + key facts"
    )
    full_content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="~4000 tokens - detailed information"
    )

    # Importance and versioning
    importance: Mapped[int] = mapped_column(
        Integer, default=0, index=True, comment="0 (useless) to 9999+ (CRITICAL)"
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, comment="Version number for tracking changes"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Original memory ID if this is an update"
    )

    # Creator and timestamps
    created_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="User ID who created this memory"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Access tracking for optimization
    last_accessed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last time memory was retrieved"
    )
    access_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Number of times memory was accessed"
    )

    # Relationships
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=memory_category_association,
        back_populates="memories",
    )

    def __repr__(self):
        content_preview = self.simple_content[:50] if self.simple_content else ""
        cats = [c.name for c in self.categories] if self.categories else []
        return (
            f"<Memory(id={self.id}, importance={self.importance}, "
            f"categories={cats}, content='{content_preview}...')>"
        )


class Category(Base):
    """Category model for organizing memories.

    Predefined categories:
    - person, event, emotion, interest, fact, skill, goal, problem, location, custom
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True, comment="Category name (unique)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Category description"
    )
    icon: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Emoji icon for category"
    )

    # Relationships
    memories: Mapped[list["Memory"]] = relationship(
        "Memory",
        secondary=memory_category_association,
        back_populates="categories",
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', icon='{self.icon}')>"
