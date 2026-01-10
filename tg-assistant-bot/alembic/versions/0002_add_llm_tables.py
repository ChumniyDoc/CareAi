"""add llm tables

Revision ID: 0002_add_llm_tables
Revises: 0001_init
Create Date: 2024-06-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_llm_tables"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profile_summaries",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "llm_interaction_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_text", sa.Text(), nullable=False),
        sa.Column("assistant_text", sa.Text(), nullable=False),
        sa.Column("tool_calls_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_llm_interaction_logs_user_id", "llm_interaction_logs", ["user_id"])
    op.create_table(
        "pending_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tool_name", sa.String(length=64), nullable=False),
        sa.Column("tool_args_json", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pending_actions_user_id", "pending_actions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_pending_actions_user_id", table_name="pending_actions")
    op.drop_table("pending_actions")
    op.drop_index("ix_llm_interaction_logs_user_id", table_name="llm_interaction_logs")
    op.drop_table("llm_interaction_logs")
    op.drop_table("user_profile_summaries")
