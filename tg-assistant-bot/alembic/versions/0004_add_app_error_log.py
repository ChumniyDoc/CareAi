"""add app error log

Revision ID: 0004_add_app_error_log
Revises: 0003_add_user_state
Create Date: 2024-06-01 00:00:02.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_add_app_error_log"
down_revision = "0003_add_user_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_error_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("module", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stacktrace", sa.Text(), nullable=False),
        sa.Column("context_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_app_error_logs_ts", "app_error_logs", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_app_error_logs_ts", table_name="app_error_logs")
    op.drop_table("app_error_logs")
