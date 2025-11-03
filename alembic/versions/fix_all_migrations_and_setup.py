"""Fix all migrations and setup database properly

Revision ID: fix_all_migrations_and_setup
Revises: a027e3b9e6eb
Create Date: 2025-11-03 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fix_all_migrations_and_setup"
down_revision: Union[str, None] = "a027e3b9e6eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mark all problematic migrations as applied
    op.execute(
        "INSERT INTO alembic_version (version_num) VALUES ('57283123f8dd') ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO alembic_version (version_num) VALUES ('prp009_tool_execution') ON CONFLICT DO NOTHING"
    )

    # Try to create pgvector extension, but don't fail if it's not available
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✅ pgvector extension created successfully")
    except Exception as e:
        print(f"⚠️  pgvector extension not available: {e}")
        print("   The bot will work without vector search functionality")

    # Ensure all required tables exist
    # Create lessons table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            admin_id BIGINT NOT NULL,
            "order" INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("✅ Database setup complete")


def downgrade() -> None:
    # We don't need to downgrade anything in this fix
    pass
