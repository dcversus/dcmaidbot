"""add_vad_emotions_and_zettelkasten_to_memory

Revision ID: d22372cca607
Revises: 44578e522386
Create Date: 2025-10-29 13:06:22.000000

Adds VAD (Valence-Arousal-Dominance) emotions and Zettelkasten
attributes to Memory model. Based on PRP-005 research: A-MEM
(NeurIPS 2025), VAD Model, Knowledge Graphs.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d22372cca607"
down_revision: Union[str, None] = "44578e522386"
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
    """Add VAD emotions, Zettelkasten attributes, and MemoryLink table."""

    # Check if tables exist, create them if not
    # (handles case where previous migration was empty)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create memories table if it doesn't exist
    if "memories" not in existing_tables:
        op.create_table(
            "memories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("simple_content", sa.Text(), nullable=False),
            sa.Column("full_content", sa.Text(), nullable=False),
            sa.Column("importance", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.BigInteger(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("last_accessed", sa.DateTime(), nullable=True),
            sa.Column("access_count", sa.Integer(), nullable=True, server_default="0"),
            sa.ForeignKeyConstraint(
                ["parent_id"],
                ["memories.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_memories_importance"), "memories", ["importance"], unique=False
        )

    # Create categories table if it doesn't exist
    if "categories" not in existing_tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("icon", sa.String(length=10), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    # Create memory_category_association if it doesn't exist
    if "memory_category_association" not in existing_tables:
        op.create_table(
            "memory_category_association",
            sa.Column("memory_id", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["category_id"], ["categories.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("memory_id", "category_id"),
        )

    # Add VAD (Valence-Arousal-Dominance) emotion fields to memories table
    if not column_exists("memories", "emotion_valence"):
        op.add_column(
            "memories", sa.Column("emotion_valence", sa.Float(), nullable=True)
        )
    if not column_exists("memories", "emotion_arousal"):
        op.add_column(
            "memories", sa.Column("emotion_arousal", sa.Float(), nullable=True)
        )
    if not column_exists("memories", "emotion_dominance"):
        op.add_column(
            "memories", sa.Column("emotion_dominance", sa.Float(), nullable=True)
        )
    if not column_exists("memories", "emotion_label"):
        op.add_column(
            "memories", sa.Column("emotion_label", sa.String(length=50), nullable=True)
        )

    # Add Zettelkasten attributes to memories table
    # Note: SQLite doesn't support ARRAY type, so we use JSON for development
    # Production PostgreSQL will use actual ARRAY type
    if not column_exists("memories", "keywords"):
        try:
            # Try PostgreSQL ARRAY (production)
            op.add_column(
                "memories",
                sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
            )
        except Exception:
            # Fallback to TEXT for SQLite (development)
            op.add_column("memories", sa.Column("keywords", sa.Text(), nullable=True))

    if not column_exists("memories", "tags"):
        try:
            op.add_column(
                "memories",
                sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
            )
        except Exception:
            op.add_column("memories", sa.Column("tags", sa.Text(), nullable=True))

    if not column_exists("memories", "evolution_triggers"):
        try:
            op.add_column(
                "memories",
                sa.Column(
                    "evolution_triggers", postgresql.ARRAY(sa.Integer()), nullable=True
                ),
            )
        except Exception:
            op.add_column(
                "memories", sa.Column("evolution_triggers", sa.Text(), nullable=True)
            )

    if not column_exists("memories", "context_temporal"):
        op.add_column(
            "memories", sa.Column("context_temporal", sa.Text(), nullable=True)
        )
    if not column_exists("memories", "context_situational"):
        op.add_column(
            "memories", sa.Column("context_situational", sa.Text(), nullable=True)
        )

    # Add index on created_at for temporal queries
    if not index_exists("memories", "ix_memories_created_at"):
        op.create_index(
            op.f("ix_memories_created_at"), "memories", ["created_at"], unique=False
        )

    # Enhance categories table with domain-based hierarchy
    if not column_exists("categories", "domain"):
        op.add_column(
            "categories", sa.Column("domain", sa.String(length=50), nullable=True)
        )
    if not column_exists("categories", "full_path"):
        op.add_column(
            "categories", sa.Column("full_path", sa.String(length=200), nullable=True)
        )
    if not column_exists("categories", "importance_range_min"):
        op.add_column(
            "categories",
            sa.Column(
                "importance_range_min", sa.Integer(), nullable=True, server_default="0"
            ),
        )
    if not column_exists("categories", "importance_range_max"):
        op.add_column(
            "categories",
            sa.Column(
                "importance_range_max",
                sa.Integer(),
                nullable=True,
                server_default="10000",
            ),
        )
    if not column_exists("categories", "parent_id"):
        op.add_column("categories", sa.Column("parent_id", sa.Integer(), nullable=True))

    # Add foreign key for category hierarchy (skip for SQLite)
    if conn.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_categories_parent", "categories", "categories", ["parent_id"], ["id"]
        )

    # Create indexes on new category fields
    if not index_exists("categories", "ix_categories_name"):
        op.create_index(
            op.f("ix_categories_name"), "categories", ["name"], unique=False
        )
    if not index_exists("categories", "ix_categories_domain"):
        op.create_index(
            op.f("ix_categories_domain"), "categories", ["domain"], unique=False
        )

    # Update existing categories to have domain and full_path
    # This will be filled in by the seed_categories script
    update_sql = (
        "UPDATE categories SET domain = 'general', "
        "full_path = name WHERE domain IS NULL"
    )
    op.execute(update_sql)

    # Now make these fields non-nullable
    # (skip for SQLite - it doesn't support ALTER COLUMN)
    if conn.dialect.name != "sqlite":
        op.alter_column("categories", "domain", nullable=False)
        op.alter_column("categories", "full_path", nullable=False)

    # Add unique constraint on full_path (skip if exists)
    try:
        op.create_unique_constraint(
            "uq_categories_full_path", "categories", ["full_path"]
        )
    except Exception:
        pass  # Constraint already exists

    # Update CASCADE behavior for memory_category_association
    # Drop and recreate with CASCADE
    op.drop_table("memory_category_association")
    op.create_table(
        "memory_category_association",
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("memory_id", "category_id"),
    )

    # Create memory_links table (Zettelkasten-style bidirectional links)
    op.create_table(
        "memory_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_memory_id", sa.Integer(), nullable=False),
        sa.Column("to_memory_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=50), nullable=False),
        sa.Column("strength", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("auto_generated", sa.Boolean(), nullable=True, server_default="0"),
        sa.ForeignKeyConstraint(
            ["from_memory_id"],
            ["memories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["to_memory_id"],
            ["memories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_memory_id", "to_memory_id", "link_type", name="unique_memory_link"
        ),
    )

    # Create indexes on memory_links for efficient queries
    if not index_exists("memory_links", "ix_memory_links_from_memory_id"):
        op.create_index(
            op.f("ix_memory_links_from_memory_id"),
            "memory_links",
            ["from_memory_id"],
            unique=False,
        )
    if not index_exists("memory_links", "ix_memory_links_to_memory_id"):
        op.create_index(
            op.f("ix_memory_links_to_memory_id"),
            "memory_links",
            ["to_memory_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove VAD emotions, Zettelkasten attributes, and MemoryLink table."""

    # Drop memory_links table
    op.drop_index(op.f("ix_memory_links_to_memory_id"), table_name="memory_links")
    op.drop_index(op.f("ix_memory_links_from_memory_id"), table_name="memory_links")
    op.drop_table("memory_links")

    # Restore original memory_category_association (without CASCADE)
    op.drop_table("memory_category_association")
    op.create_table(
        "memory_category_association",
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["memories.id"],
        ),
        sa.PrimaryKeyConstraint("memory_id", "category_id"),
    )

    # Drop category enhancements
    op.drop_constraint("uq_categories_full_path", "categories", type_="unique")
    op.drop_constraint("fk_categories_parent", "categories", type_="foreignkey")
    op.drop_index(op.f("ix_categories_domain"), table_name="categories")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_column("categories", "parent_id")
    op.drop_column("categories", "importance_range_max")
    op.drop_column("categories", "importance_range_min")
    op.drop_column("categories", "full_path")
    op.drop_column("categories", "domain")

    # Drop memory enhancements
    op.drop_index(op.f("ix_memories_created_at"), table_name="memories")
    op.drop_column("memories", "context_situational")
    op.drop_column("memories", "context_temporal")
    op.drop_column("memories", "evolution_triggers")
    op.drop_column("memories", "tags")
    op.drop_column("memories", "keywords")
    op.drop_column("memories", "emotion_label")
    op.drop_column("memories", "emotion_dominance")
    op.drop_column("memories", "emotion_arousal")
    op.drop_column("memories", "emotion_valence")
