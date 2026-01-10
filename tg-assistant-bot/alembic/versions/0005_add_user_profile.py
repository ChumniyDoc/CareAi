"""add user profile

Revision ID: 0005_add_user_profile
Revises: 0004_add_app_error_log
Create Date: 2024-06-01 00:00:03.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_add_user_profile"
down_revision = "0004_add_app_error_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'Asia/Almaty'"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
