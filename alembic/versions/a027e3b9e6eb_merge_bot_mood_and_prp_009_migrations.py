"""Merge bot mood and PRP-009 migrations

Revision ID: a027e3b9e6eb
Revises: create_bot_mood_tables, prp009_tool_execution
Create Date: 2025-11-03 14:56:09.219802

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a027e3b9e6eb"
down_revision: Union[str, Sequence[str], None] = (
    "create_bot_mood_tables",
    "prp009_tool_execution",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
