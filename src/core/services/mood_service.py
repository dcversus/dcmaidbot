"""Mood and emotional state management service.

This service manages the bot's emotional state, tracks moods,
and updates relationships with users based on interactions.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.bot_state import BotMood, UserRelationship
from core.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class MoodService:
    """Service for managing bot's mood and emotional state."""

    CACHE_PREFIX = "mood"
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, session: AsyncSession):
        """
        Initialize mood service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_current_mood(self) -> BotMood:
        """Get the bot's current mood state."""
        # Try cache first
        cached = await redis_service.get(f"{self.CACHE_PREFIX}:current")
        if cached:
            mood_data = json.loads(cached)
            return BotMood(**mood_data)

        # Get from database
        result = await self.session.execute(
            select(BotMood).order_by(desc(BotMood.last_updated)).limit(1)
        )
        mood = result.scalar_one_or_none()

        if not mood:
            # Create initial mood
            mood = BotMood(
                valence=0.0,
                arousal=0.0,
                dominance=0.0,
                primary_mood="neutral",
                mood_intensity=0.5,
                energy_level=0.7,
                social_engagement=0.5,
                confidence=0.6,
                mood_reason="Just started up, ready to chat! ^-^",
                last_updated=datetime.utcnow(),
            )
            self.session.add(mood)
            await self.session.commit()
            await self.session.refresh(mood)

        # Cache the mood
        await redis_service.setex(
            f"{self.CACHE_PREFIX}:current",
            self.CACHE_TTL,
            json.dumps(
                {
                    "id": mood.id,
                    "valence": mood.valence,
                    "arousal": mood.arousal,
                    "dominance": mood.dominance,
                    "primary_mood": mood.primary_mood,
                    "mood_intensity": mood.mood_intensity,
                    "energy_level": mood.energy_level,
                    "social_engagement": mood.social_engagement,
                    "confidence": mood.confidence,
                    "last_interaction": mood.last_interaction.isoformat()
                    if mood.last_interaction
                    else None,
                    "interaction_count": mood.interaction_count,
                    "recent_memories_count": mood.recent_memories_count,
                    "mood_reason": mood.mood_reason,
                    "last_updated": mood.last_updated.isoformat(),
                    "triggered_by_memory_id": mood.triggered_by_memory_id,
                    "triggered_by_user_id": mood.triggered_by_user_id,
                }
            ),
        )

        return mood

    async def update_mood(
        self,
        valence_change: Optional[float] = None,
        arousal_change: Optional[float] = None,
        dominance_change: Optional[float] = None,
        energy_change: Optional[float] = None,
        social_change: Optional[float] = None,
        confidence_change: Optional[float] = None,
        reason: Optional[str] = None,
        user_id: Optional[int] = None,
        memory_id: Optional[int] = None,
    ) -> BotMood:
        """Update the bot's mood based on new interaction."""
        mood = await self.get_current_mood()

        # Apply changes with bounds checking
        if valence_change is not None:
            mood.valence = max(-1.0, min(1.0, mood.valence + valence_change))
        if arousal_change is not None:
            mood.arousal = max(-1.0, min(1.0, mood.arousal + arousal_change))
        if dominance_change is not None:
            mood.dominance = max(-1.0, min(1.0, mood.dominance + dominance_change))
        if energy_change is not None:
            mood.energy_level = max(0.0, min(1.0, mood.energy_level + energy_change))
        if social_change is not None:
            mood.social_engagement = max(
                0.0, min(1.0, mood.social_engagement + social_change)
            )
        if confidence_change is not None:
            mood.confidence = max(0.0, min(1.0, mood.confidence + confidence_change))

        # Update primary mood based on VAD values
        mood.primary_mood = self._determine_primary_mood(
            mood.valence, mood.arousal, mood.dominance
        )
        mood.mood_intensity = self._calculate_mood_intensity(
            mood.valence, mood.arousal, mood.dominance
        )

        # Update metadata
        mood.last_interaction = datetime.utcnow()
        mood.interaction_count += 1
        if reason:
            mood.mood_reason = reason
        if memory_id:
            mood.triggered_by_memory_id = memory_id
        if user_id:
            mood.triggered_by_user_id = user_id

        mood.last_updated = datetime.utcnow()

        # Save and cache
        self.session.add(mood)
        await self.session.commit()

        # Invalidate cache
        await redis_service.delete(f"{self.CACHE_PREFIX}:current")

        return mood

    def _determine_primary_mood(
        self, valence: float, arousal: float, dominance: float
    ) -> str:
        """Determine primary mood from VAD values."""
        # High valence (positive)
        if valence > 0.5:
            if arousal > 0.5:
                return "excited" if dominance > 0 else "happy"
            else:
                return "content" if dominance > 0 else "calm"
        # Low valence (negative)
        elif valence < -0.5:
            if arousal > 0.5:
                return "angry" if dominance > 0 else "anxious"
            else:
                return "sad" if dominance > 0 else "tired"
        # Neutral valence
        else:
            if arousal > 0.5:
                return "alert"
            elif arousal < -0.5:
                return "bored"
            else:
                return "neutral"

    def _calculate_mood_intensity(
        self, valence: float, arousal: float, dominance: float
    ) -> float:
        """Calculate overall mood intensity from VAD values."""
        # Use Euclidean distance from center (0,0,0)
        return min(1.0, (valence**2 + arousal**2 + dominance**2) ** 0.5)

    async def get_user_relationship(self, user_id: int) -> UserRelationship:
        """Get or create relationship with a user."""
        # Try cache first
        cached = await redis_service.get(f"{self.CACHE_PREFIX}:relationship:{user_id}")
        if cached:
            rel_data = json.loads(cached)
            return UserRelationship(**rel_data)

        # Get from database
        result = await self.session.execute(
            select(UserRelationship).where(UserRelationship.user_id == user_id)
        )
        rel = result.scalar_one_or_none()

        if not rel:
            # Create new relationship
            rel = UserRelationship(
                user_id=user_id,
                trust_score=0.5,
                friendship_level=0.3,
                familiarity=0.0,
                relationship_type="user"
                if user_id
                not in [
                    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
                ]
                else "admin",
                bot_feeling="curious",
                created_at=datetime.utcnow(),
            )
            self.session.add(rel)
            await self.session.commit()
            await self.session.refresh(rel)

        # Cache the relationship
        await redis_service.setex(
            f"{self.CACHE_PREFIX}:relationship:{user_id}",
            self.CACHE_TTL,
            json.dumps(
                {
                    "id": rel.id,
                    "user_id": rel.user_id,
                    "trust_score": rel.trust_score,
                    "friendship_level": rel.friendship_level,
                    "familiarity": rel.familiarity,
                    "total_interactions": rel.total_interactions,
                    "positive_interactions": rel.positive_interactions,
                    "last_interaction": rel.last_interaction.isoformat()
                    if rel.last_interaction
                    else None,
                    "preferred_style": rel.preferred_style,
                    "communication_frequency": rel.communication_frequency,
                    "relationship_type": rel.relationship_type,
                    "bot_feeling": rel.bot_feeling,
                    "created_at": rel.created_at.isoformat(),
                    "updated_at": rel.updated_at.isoformat(),
                }
            ),
        )

        return rel

    async def update_relationship(
        self,
        user_id: int,
        trust_change: Optional[float] = None,
        friendship_change: Optional[float] = None,
        familiarity_change: Optional[float] = None,
        is_positive: bool = True,
        interaction_type: str = "chat",
    ) -> UserRelationship:
        """Update relationship with a user after interaction."""
        rel = await self.get_user_relationship(user_id)

        # Apply changes
        if trust_change is not None:
            rel.trust_score = max(0.0, min(1.0, rel.trust_score + trust_change))
        if friendship_change is not None:
            rel.friendship_level = max(
                0.0, min(1.0, rel.friendship_level + friendship_change)
            )
        if familiarity_change is not None:
            rel.familiarity = max(0.0, min(1.0, rel.familiarity + familiarity_change))

        # Update interaction counts
        rel.total_interactions += 1
        if is_positive:
            rel.positive_interactions += 1

        # Update frequency
        now = datetime.utcnow()
        if rel.last_interaction:
            time_diff = now - rel.last_interaction
            # Simple moving average for interactions per day
            rel.communication_frequency = (
                rel.communication_frequency * 0.9
                + (86400 / time_diff.total_seconds()) * 0.1
            )
        rel.last_interaction = now

        # Update bot feeling based on relationship metrics
        if rel.trust_score > 0.8 and rel.friendship_level > 0.7:
            rel.bot_feeling = "close friend"
        elif rel.trust_score > 0.6:
            rel.bot_feeling = "friend"
        elif rel.trust_score > 0.4:
            rel.bot_feeling = "friendly"
        elif rel.trust_score > 0.2:
            rel.bot_feeling = "acquaintance"
        else:
            rel.bot_feeling = "stranger"

        # Update relationship type based on admin status
        admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        if user_id in admin_ids:
            rel.relationship_type = "admin"

        rel.updated_at = now

        # Save and cache
        self.session.add(rel)
        await self.session.commit()

        # Invalidate cache
        await redis_service.delete(f"{self.CACHE_PREFIX}:relationship:{user_id}")

        return rel

    async def get_mood_summary(self) -> dict[str, Any]:
        """Get a summary of current mood state for display."""
        mood = await self.get_current_mood()

        # Get mood emoji
        mood_emoji = {
            "happy": "😊",
            "excited": "🎉",
            "content": "😌",
            "calm": "😊",
            "sad": "😢",
            "angry": "😠",
            "anxious": "😰",
            "tired": "😴",
            "alert": "👀",
            "bored": "😑",
            "neutral": "😐",
        }.get(mood.primary_mood, "😐")

        # Get energy level description
        energy_desc = (
            "Low"
            if mood.energy_level < 0.3
            else "Medium"
            if mood.energy_level < 0.7
            else "High"
        )

        # Get confidence description
        confidence_desc = (
            "Shy"
            if mood.confidence < 0.3
            else "Modest"
            if mood.confidence < 0.7
            else "Confident"
        )

        return {
            "mood_emoji": mood_emoji,
            "primary_mood": mood.primary_mood.capitalize(),
            "mood_intensity": f"{mood.mood_intensity:.1%}",
            "energy_level": energy_desc,
            "energy_value": f"{mood.energy_level:.1%}",
            "confidence": confidence_desc,
            "confidence_value": f"{mood.confidence:.1%}",
            "social_engagement": f"{mood.social_engagement:.1%}",
            "vad_scores": {
                "valence": f"{mood.valence:+.2f}",
                "arousal": f"{mood.arousal:+.2f}",
                "dominance": f"{mood.dominance:+.2f}",
            },
            "reason": mood.mood_reason,
            "last_updated": mood.last_updated.strftime("%H:%M:%S"),
            "interaction_count": mood.interaction_count,
        }
