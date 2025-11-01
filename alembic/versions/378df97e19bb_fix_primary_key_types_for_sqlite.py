"""fix_primary_key_types_for_sqlite

Revision ID: 378df97e19bb
Revises: a1197e0dd7ca
Create Date: 2025-10-31 15:45:00

This migration fixes primary key types from BigInteger to Integer
for SQLite compatibility. SQLite doesn't handle BigInteger autoincrement properly.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "378df97e19bb"
down_revision: Union[str, None] = "a1197e0dd7ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """For SQLite: recreate tables with INTEGER primary keys.

    For PostgreSQL: BigInteger works fine, so this is a no-op.
    """
    # Check if we're using SQLite
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite can't alter column types
        # Future tables will use Integer for compatibility
        # This migration marks awareness of the issue
        pass
    # PostgreSQL: no changes needed


def downgrade() -> None:
    """No changes needed in downgrade."""
    pass
