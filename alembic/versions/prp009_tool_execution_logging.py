"""Add tool execution logging for PRP-009

Revision ID: prp009_tool_execution
Revises: 57283123f8dd
Create Date: 2025-11-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "prp009_tool_execution"
down_revision: Union[str, None] = "57283123f8dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tool_executions table for PRP-009 external tools logging."""
    # Create tool_executions table
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("parameters", sa.Text(), nullable=False),
        sa.Column("request_timestamp", sa.DateTime(), nullable=True),
        sa.Column("response_data", sa.Text(), nullable=True),
        sa.Column("response_timestamp", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index(
        op.f("ix_tool_executions_tool_name"),
        "tool_executions",
        ["tool_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tool_executions_user_id"), "tool_executions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_tool_executions_chat_id"), "tool_executions", ["chat_id"], unique=False
    )
    op.create_index(
        op.f("ix_tool_executions_request_timestamp"),
        "tool_executions",
        ["request_timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Remove tool_executions table."""
    op.drop_index(
        op.f("ix_tool_executions_request_timestamp"), table_name="tool_executions"
    )
    op.drop_index(op.f("ix_tool_executions_chat_id"), table_name="tool_executions")
    op.drop_index(op.f("ix_tool_executions_user_id"), table_name="tool_executions")
    op.drop_index(op.f("ix_tool_executions_tool_name"), table_name="tool_executions")
    op.drop_table("tool_executions")
