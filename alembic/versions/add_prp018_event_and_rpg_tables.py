"""Add event collection and RPG system tables.

Revision ID: add_prp018_event_and_rpg_tables
Revises: 378df97e19bb
Create Date: 2025-11-01 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_prp018_event_and_rpg_tables"
down_revision: Union[str, None] = "378df97e19bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create event collection and RPG system tables."""

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("key_prefix", sa.String(length=8), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=True, default=0),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True, default=60),
        sa.Column("rate_limit_per_hour", sa.Integer(), nullable=True, default=1000),
        sa.Column("allowed_event_types", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_api_keys_key_hash", "key_hash", unique=True),
        sa.Index("ix_api_keys_is_active", "is_active"),
        sa.Index("ix_api_keys_created_at", "created_at"),
        sa.Index("ix_api_keys_created_by", "created_by"),
    )

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_subtype", sa.String(length=50), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("button_text", sa.String(length=200), nullable=True),
        sa.Column("callback_data", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, default="unread"),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("processing_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_events_event_id", "event_id", unique=True),
        sa.Index("ix_events_user_id", "user_id"),
        sa.Index("ix_events_chat_id", "chat_id"),
        sa.Index("ix_events_event_type", "event_type"),
        sa.Index("ix_events_status", "status"),
        sa.Index("ix_events_created_at", "created_at"),
    )

    # Create game_sessions table
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("game_master_id", sa.Integer(), nullable=False),
        sa.Column("scenario_template", sa.Text(), nullable=False),
        sa.Column(
            "difficulty_level", sa.String(length=20), nullable=False, default="normal"
        ),
        sa.Column("current_step", sa.Integer(), nullable=False, default=1),
        sa.Column("max_players", sa.Integer(), nullable=False, default=4),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_paused", sa.Boolean(), nullable=False, default=False),
        sa.Column("hidden_context", sa.JSON(), nullable=False, default={}),
        sa.Column("game_state", sa.JSON(), nullable=False, default={}),
        sa.Column("world_data", sa.JSON(), nullable=False, default={}),
        sa.Column("step_timeout_minutes", sa.Integer(), nullable=False, default=60),
        sa.Column("last_activity_at", sa.DateTime(), nullable=True),
        sa.Column("auto_progress_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_game_sessions_session_id", "session_id", unique=True),
        sa.Index("ix_game_sessions_is_active", "is_active"),
        sa.Index("ix_game_sessions_created_at", "created_at"),
        sa.Index("ix_game_sessions_created_by", "created_by"),
    )

    # Create player_states table
    op.create_table(
        "player_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("character_name", sa.String(length=100), nullable=False),
        sa.Column("character_class", sa.String(length=50), nullable=True),
        sa.Column("character_description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("current_location", sa.String(length=100), nullable=True),
        sa.Column("health_points", sa.Integer(), nullable=False, default=100),
        sa.Column("mana_points", sa.Integer(), nullable=False, default=50),
        sa.Column("inventory", sa.JSON(), nullable=False, default={}),
        sa.Column("stats", sa.JSON(), nullable=False, default={}),
        sa.Column("achievements", sa.JSON(), nullable=False, default={}),
        sa.Column("choices_history", sa.JSON(), nullable=False, default={}),
        sa.Column("consequences", sa.JSON(), nullable=False, default={}),
        sa.Column("current_step", sa.Integer(), nullable=False, default=1),
        sa.Column("completed_steps", sa.JSON(), nullable=False, default=[]),
        sa.Column("available_actions", sa.JSON(), nullable=False, default=[]),
        sa.Column("player_memory", sa.JSON(), nullable=False, default={}),
        sa.Column("discovered_locations", sa.JSON(), nullable=False, default=[]),
        sa.Column("met_characters", sa.JSON(), nullable=False, default=[]),
        sa.Column("last_action_at", sa.DateTime(), nullable=True),
        sa.Column("actions_taken", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_player_states_user_id", "user_id"),
        sa.Index("ix_player_states_session_id", "session_id"),
        sa.Index("ix_player_states_is_active", "is_active"),
        sa.Index("ix_player_states_created_at", "created_at"),
    )


def downgrade() -> None:
    """Drop event collection and RPG system tables."""

    # Drop tables in reverse order of creation
    op.drop_table("player_states")
    op.drop_table("game_sessions")
    op.drop_table("events")
    op.drop_table("api_keys")
