"""add_pgvector_extension_and_embedding_column_for_prp_007

Revision ID: 57283123f8dd
Revises: add_prp018_event_and_rpg_tables
Create Date: 2025-11-01 18:42:47.281485

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "57283123f8dd"
down_revision: Union[str, Sequence[str], None] = "7dd480bd6210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for PRP-007: Add embedding column for vector search."""
    # Add embedding column as JSONB for efficient storage and querying
    # JSONB is native to PostgreSQL and doesn't require extensions
    # It provides efficient indexing and JSON operations
    op.add_column("memories", sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove embedding column
    op.drop_column("memories", "embedding")

    # Note: We don't drop the pgvector extension as other tables might use it
    # This would require manual intervention if needed
