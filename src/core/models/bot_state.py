"""Bot state and mood tracking model for emotional intelligence.

This model tracks the bot's emotional state based on interactions,
memories, and conversation patterns.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.services.database import Base


class BotMood(Base):
    """Track bot's current mood and emotional state."""

    __tablename__ = "bot_moods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # VAD emotional state (Valence-Arousal-Dominance)
    valence: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # -1.0 (sad) to +1.0 (happy)
    arousal: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # -1.0 (tired) to +1.0 (energetic)
    dominance: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # -1.0 (submissive) to +1.0 (confident)

    # Mood descriptors
    primary_mood: Mapped[str] = mapped_column(
        String(50), default="neutral"
    )  # happy, sad, excited, tired, etc.
    mood_intensity: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0

    # Contextual factors
    energy_level: Mapped[float] = mapped_column(Float, default=0.7)  # 0.0 to 1.0
    social_engagement: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    confidence: Mapped[float] = mapped_column(Float, default=0.6)  # 0.0 to 1.0

    # Metadata
    last_interaction: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    recent_memories_count: Mapped[int] = mapped_column(Integer, default=0)

    # Reasoning for current mood
    mood_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Influences
    triggered_by_memory_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    triggered_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )


class UserRelationship(Base):
    """Track bot's relationship with individual users."""

    __tablename__ = "user_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # Relationship metrics
    trust_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    friendship_level: Mapped[float] = mapped_column(Float, default=0.3)  # 0.0 to 1.0
    familiarity: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0

    # Interaction patterns
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    positive_interactions: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # User preferences learned from interactions
    preferred_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    communication_frequency: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # interactions per day

    # Relationship type
    relationship_type: Mapped[str] = mapped_column(
        String(50), default="user"
    )  # admin, friend, user, etc.

    # Bot's feeling toward user
    bot_feeling: Mapped[str] = mapped_column(
        String(50), default="neutral"
    )  # likes, trusts, wary, etc.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
