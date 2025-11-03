"""Create bot mood and relationship tables

Revision ID: create_bot_mood_tables
Revises: a1197e0dd7ca
Create Date: 2025-11-03 22:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_bot_mood_tables"
down_revision: Union[str, None] = "a1197e0dd7ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bot_moods table
    op.create_table(
        "bot_moods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("valence", sa.Float(), nullable=True),
        sa.Column("arousal", sa.Float(), nullable=True),
        sa.Column("dominance", sa.Float(), nullable=True),
        sa.Column("primary_mood", sa.String(length=50), nullable=True),
        sa.Column("mood_intensity", sa.Float(), nullable=True),
        sa.Column("energy_level", sa.Float(), nullable=True),
        sa.Column("social_engagement", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("last_interaction", sa.DateTime(), nullable=True),
        sa.Column("interaction_count", sa.Integer(), nullable=True),
        sa.Column("recent_memories_count", sa.Integer(), nullable=True),
        sa.Column("mood_reason", sa.Text(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("triggered_by_memory_id", sa.Integer(), nullable=True),
        sa.Column("triggered_by_user_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_moods_id"), "bot_moods", ["id"], unique=False)

    # Create user_relationships table
    op.create_table(
        "user_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("friendship_level", sa.Float(), nullable=True),
        sa.Column("familiarity", sa.Float(), nullable=True),
        sa.Column("total_interactions", sa.Integer(), nullable=True),
        sa.Column("positive_interactions", sa.Integer(), nullable=True),
        sa.Column("last_interaction", sa.DateTime(), nullable=True),
        sa.Column("preferred_style", sa.String(length=100), nullable=True),
        sa.Column("communication_frequency", sa.Float(), nullable=True),
        sa.Column("relationship_type", sa.String(length=50), nullable=True),
        sa.Column("bot_feeling", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_relationships_user_id"),
        "user_relationships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop tables
    op.drop_index(
        op.f("ix_user_relationships_user_id"), table_name="user_relationships"
    )
    op.drop_table("user_relationships")
    op.drop_index(op.f("ix_bot_moods_id"), table_name="bot_moods")
    op.drop_table("bot_moods")
