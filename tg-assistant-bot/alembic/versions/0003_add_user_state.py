"""add user state

Revision ID: 0003_add_user_state
Revises: 0002_add_llm_tables
Create Date: 2024-06-01 00:00:01.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_add_user_state"
down_revision = "0002_add_llm_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_states",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_states")
