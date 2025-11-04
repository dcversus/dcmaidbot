"""Game session models for text RPG system.

These models manage multiplayer text RPG sessions where dcmaidbot
acts as game master with hidden context buffer as memory.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.services.database import Base


class GameSession(Base):
    """Game session model for managing text RPG games."""

    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Session identification
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Game master (dcmaidbot) configuration
    game_master_id: Mapped[int] = mapped_column(
        nullable=False
    )  # Always dcmaidbot's user ID
    scenario_template: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="normal"
    )  # easy, normal, hard, expert

    # Session state
    current_step: Mapped[int] = mapped_column(default=1)
    max_players: Mapped[int] = mapped_column(default=4)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    is_paused: Mapped[bool] = mapped_column(default=False)

    # Hidden context buffer (game master memory)
    hidden_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    game_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    world_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timing and progression
    step_timeout_minutes: Mapped[int] = mapped_column(
        default=60
    )  # Auto-progress if no action
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    auto_progress_enabled: Mapped[bool] = mapped_column(default=True)

    # Created by (which admin started this session)
    created_by: Mapped[int] = mapped_column(nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"GameSession(id={self.id}, session_id='{self.session_id}', "
            f"name='{self.name}', step={self.current_step}, active={self.is_active})"
        )

    def is_joinable(self) -> bool:
        """Check if new players can join this session."""
        return (
            self.is_active
            and not self.is_paused
            and len(self.get_active_players()) < self.max_players
        )

    def get_active_players(self) -> list:
        """Get list of active player user IDs."""
        # This would be implemented with a relationship to PlayerState
        # For now, return empty list
        return []

    def is_timeout_reached(self) -> bool:
        """Check if the session has timed out due to inactivity."""
        if not self.last_activity_at or not self.auto_progress_enabled:
            return False

        timeout = datetime.utcnow() - self.last_activity_at
        return timeout.total_seconds() > (self.step_timeout_minutes * 60)

    def to_dict(self, include_hidden: bool = False) -> dict:
        """Convert game session to dictionary representation."""
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "description": self.description,
            "game_master_id": self.game_master_id,
            "difficulty_level": self.difficulty_level,
            "current_step": self.current_step,
            "max_players": self.max_players,
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "game_state": self.game_state,
            "world_data": self.world_data,
            "step_timeout_minutes": self.step_timeout_minutes,
            "last_activity_at": self.last_activity_at.isoformat()
            if self.last_activity_at
            else None,
            "auto_progress_enabled": self.auto_progress_enabled,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

        if include_hidden:
            result["hidden_context"] = self.hidden_context
            result["scenario_template"] = self.scenario_template

        return result


class PlayerState(Base):
    """Player state model for tracking individual player progress in RPG sessions."""

    __tablename__ = "player_states"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Player identification
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Player character info
    character_name: Mapped[str] = mapped_column(String(100), nullable=False)
    character_class: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    character_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Player state
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    current_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    health_points: Mapped[int] = mapped_column(default=100)
    mana_points: Mapped[int] = mapped_column(default=50)

    # Player inventory and stats
    inventory: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    stats: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    achievements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Player choices and consequences
    choices_history: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    consequences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Game progression
    current_step: Mapped[int] = mapped_column(default=1)
    completed_steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    available_actions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Player memory (what the player knows)
    player_memory: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    discovered_locations: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    met_characters: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Timing
    last_action_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    actions_taken: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"PlayerState(id={self.id}, user_id={self.user_id}, "
            f"session_id='{self.session_id}', character='{self.character_name}', "
            f"active={self.is_active})"
        )

    def is_alive(self) -> bool:
        """Check if the player character is still alive."""
        return self.health_points > 0

    def can_perform_action(self, action_type: str) -> bool:
        """Check if the player can perform a specific action type."""
        if action_type not in self.available_actions:
            return False

        # Check mana requirements
        if action_type == "magic" and self.mana_points < 10:
            return False

        # Check health requirements
        if action_type in ["combat", "exploration"] and self.health_points < 20:
            return False

        return True

    def add_to_inventory(self, item: dict) -> bool:
        """Add an item to the player's inventory."""
        if "id" not in item:
            return False

        item_id = item["id"]
        if item_id not in self.inventory:
            self.inventory[item_id] = []

        self.inventory[item_id].append(item)
        return True

    def remove_from_inventory(self, item_id: str, quantity: int = 1) -> bool:
        """Remove items from the player's inventory."""
        if item_id not in self.inventory:
            return False

        if len(self.inventory[item_id]) < quantity:
            return False

        for _ in range(quantity):
            self.inventory[item_id].pop()

        if not self.inventory[item_id]:
            del self.inventory[item_id]

        return True

    def record_choice(self, step: int, choice: str, consequence: dict):
        """Record a player choice and its consequences."""
        self.choices_history[str(step)] = choice
        if str(step) not in self.consequences:
            self.consequences[str(step)] = []
        self.consequences[str(step)].append(consequence)

    def to_dict(self) -> dict:
        """Convert player state to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "character_name": self.character_name,
            "character_class": self.character_class,
            "character_description": self.character_description,
            "is_active": self.is_active,
            "current_location": self.current_location,
            "health_points": self.health_points,
            "mana_points": self.mana_points,
            "inventory": self.inventory,
            "stats": self.stats,
            "achievements": self.achievements,
            "choices_history": self.choices_history,
            "consequences": self.consequences,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "available_actions": self.available_actions,
            "player_memory": self.player_memory,
            "discovered_locations": self.discovered_locations,
            "met_characters": self.met_characters,
            "last_action_at": self.last_action_at.isoformat()
            if self.last_action_at
            else None,
            "actions_taken": self.actions_taken,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }
