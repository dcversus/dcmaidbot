"""prp_005_replace_memories_with_advanced_system

Revision ID: 25be9789ec50
Revises: 4cc559142096
Create Date: 2025-10-28 16:01:42.256230

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "25be9789ec50"
down_revision: Union[str, Sequence[str], None] = "4cc559142096"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Replace PRP-004 memories with PRP-005 advanced memory system."""

    # Drop old memories table from PRP-004 (superseded)
    op.drop_table("memories")

    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False, comment="Category name (unique)"),
        sa.Column(
            "description", sa.Text(), nullable=True, comment="Category description"
        ),
        sa.Column("icon", sa.Text(), nullable=True, comment="Emoji icon for category"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)

    # Create new memories table (PRP-005)
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "simple_content",
            sa.Text(),
            nullable=False,
            comment="~500 tokens - emotional signals + key facts",
        ),
        sa.Column(
            "full_content",
            sa.Text(),
            nullable=False,
            comment="~4000 tokens - detailed information",
        ),
        sa.Column(
            "importance",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0 (useless) to 9999+ (CRITICAL)",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Version number for tracking changes",
        ),
        sa.Column(
            "parent_id",
            sa.Integer(),
            nullable=True,
            comment="Original memory ID if this is an update",
        ),
        sa.Column(
            "created_by",
            sa.BigInteger(),
            nullable=False,
            comment="User ID who created this memory",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_accessed",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last time memory was retrieved",
        ),
        sa.Column(
            "access_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of times memory was accessed",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_importance", "memories", ["importance"], unique=False)

    # Create memory_category_association table (many-to-many)
    op.create_table(
        "memory_category_association",
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("memory_id", "category_id"),
    )


def downgrade() -> None:
    """Downgrade schema - Restore PRP-004 memories table."""

    # Drop PRP-005 tables
    op.drop_table("memory_category_association")
    op.drop_index("ix_memories_importance", table_name="memories")
    op.drop_table("memories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")

    # Recreate old memories table (PRP-004)
    op.create_table(
        "memories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "admin_id",
            sa.BigInteger(),
            nullable=False,
            comment="Admin who created memory",
        ),
        sa.Column(
            "chat_id",
            sa.BigInteger(),
            nullable=True,
            comment="Specific chat or NULL for global",
        ),
        sa.Column(
            "prompt", sa.Text(), nullable=False, comment="Instructions for bot behavior"
        ),
        sa.Column(
            "matching_expression",
            sa.String(500),
            nullable=True,
            comment="Regex or text to match",
        ),
        sa.Column(
            "action",
            sa.String(255),
            nullable=True,
            comment="Action to take when matched",
        ),
        sa.Column(
            "allowance_token",
            sa.String(100),
            nullable=True,
            comment="Token for group access",
        ),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "priority",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Higher = checked first",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("allowance_token"),
    )
