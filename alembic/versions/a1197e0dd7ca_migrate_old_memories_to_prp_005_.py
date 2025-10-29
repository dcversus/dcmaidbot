"""migrate_old_memories_to_prp_005_structure

Revision ID: a1197e0dd7ca
Revises: 9f1427b123f3
Create Date: 2025-10-29 21:05:16.219624

Migrates old memories table structure (admin_id, chat_id, prompt, etc.)
to new PRP-005 structure (simple_content, full_content, importance, etc.).

This migration:
1. Backs up old memories table as memories_old
2. Creates new memories table with PRP-005 structure
3. Keeps VAD emotions and Zettelkasten columns already added
4. Old memories_old table can be dropped manually after verification
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1197e0dd7ca"
down_revision: Union[str, Sequence[str], None] = "9f1427b123f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """Migrate old memories structure to PRP-005 structure."""
    conn = op.get_bind()

    # Check if this is the old structure (has admin_id column)
    if not column_exists("memories", "admin_id"):
        # Already migrated or never had old structure
        return

    # Step 1: Drop foreign keys and associations that reference memories table first
    # Drop memory_category_association (will recreate later)
    op.drop_table("memory_category_association")

    # Drop memory_links table (will recreate later)
    try:
        op.drop_table("memory_links")
    except Exception:
        pass  # Table might not exist

    # Step 2: Drop indexes on memories table before renaming
    # This is necessary because renaming the table doesn't rename the indexes
    if index_exists("memories", "ix_memories_created_at"):
        op.drop_index("ix_memories_created_at", table_name="memories")

    # Step 3: Rename old memories table to memories_old for backup
    op.rename_table("memories", "memories_old")

    # Step 3: Create new memories table with PRP-005 structure
    # Including VAD emotions and Zettelkasten attributes
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("simple_content", sa.Text(), nullable=False),
        sa.Column("full_content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="0"),
        # VAD emotions (from previous migration)
        sa.Column("emotion_valence", sa.Float(), nullable=True),
        sa.Column("emotion_arousal", sa.Float(), nullable=True),
        sa.Column("emotion_dominance", sa.Float(), nullable=True),
        sa.Column("emotion_label", sa.String(length=50), nullable=True),
        # Zettelkasten attributes (from previous migration)
        sa.Column(
            "keywords",
            postgresql.ARRAY(sa.String())
            if conn.dialect.name == "postgresql"
            else sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String())
            if conn.dialect.name == "postgresql"
            else sa.Text(),
            nullable=True,
        ),
        sa.Column("context_temporal", sa.Text(), nullable=True),
        sa.Column("context_situational", sa.Text(), nullable=True),
        # Versioning & Evolution
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column(
            "evolution_triggers",
            postgresql.ARRAY(sa.Integer())
            if conn.dialect.name == "postgresql"
            else sa.Text(),
            nullable=True,
        ),
        # Metadata
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["parent_id"], ["memories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_memories_importance"), "memories", ["importance"], unique=False
    )
    op.create_index(
        op.f("ix_memories_created_at"), "memories", ["created_at"], unique=False
    )

    # Step 4: Recreate memory_category_association
    op.create_table(
        "memory_category_association",
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("memory_id", "category_id"),
    )

    # Step 5: Recreate memory_links table
    op.create_table(
        "memory_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_memory_id", sa.Integer(), nullable=False),
        sa.Column("to_memory_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=50), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["from_memory_id"], ["memories.id"]),
        sa.ForeignKeyConstraint(["to_memory_id"], ["memories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_memory_id", "to_memory_id", "link_type", name="unique_memory_link"
        ),
    )

    # Create indexes on memory_links
    op.create_index(
        op.f("ix_memory_links_from_memory_id"),
        "memory_links",
        ["from_memory_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_links_to_memory_id"),
        "memory_links",
        ["to_memory_id"],
        unique=False,
    )

    # Note: Data migration from memories_old can be done manually if needed
    # The old table is kept as memories_old for reference


def downgrade() -> None:
    """Downgrade not supported - would lose data structure."""
    raise NotImplementedError(
        "Downgrade not supported for this migration. "
        "Keep memories_old table if you need to rollback."
    )
