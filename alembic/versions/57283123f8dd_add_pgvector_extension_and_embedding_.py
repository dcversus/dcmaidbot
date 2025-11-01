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
down_revision: Union[str, Sequence[str], None] = "add_prp018_event_and_rpg_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for PRP-007: Add embedding column for vector search."""
    connection = op.get_bind()

    # Check if we're using PostgreSQL
    if connection.dialect.name == "postgresql":
        # Enable pgvector extension (for future use)
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column as TEXT for all databases
    # Embeddings are stored as JSON strings for compatibility
    op.add_column("memories", sa.Column("embedding", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove embedding column
    op.drop_column("memories", "embedding")

    # Note: We don't drop the pgvector extension as other tables might use it
    # This would require manual intervention if needed
