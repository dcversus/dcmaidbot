"""add created_by to memory_links for PRP-006

Revision ID: 9f1427b123f3
Revises: d22372cca607
Create Date: 2025-10-29 14:25:37.575962

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f1427b123f3"
down_revision: Union[str, Sequence[str], None] = "d22372cca607"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add created_by field to memory_links for tracking who created links."""
    # Add created_by to memory_links if not exists
    if not column_exists("memory_links", "created_by"):
        op.add_column(
            "memory_links", sa.Column("created_by", sa.BigInteger(), nullable=True)
        )


def downgrade() -> None:
    """Remove created_by field from memory_links."""
    if column_exists("memory_links", "created_by"):
        op.drop_column("memory_links", "created_by")
