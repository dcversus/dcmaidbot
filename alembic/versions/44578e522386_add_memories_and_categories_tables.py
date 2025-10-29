"""add_memories_and_categories_tables

Revision ID: 44578e522386
Revises: 4cc559142096
Create Date: 2025-10-29 12:05:53.379956

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "44578e522386"
down_revision: Union[str, Sequence[str], None] = "4cc559142096"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
