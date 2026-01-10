"""init

Revision ID: 0001_init
Revises: 
Create Date: 2024-05-20 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("morning_time", sa.String(length=5), nullable=False, server_default="09:00"),
        sa.Column("evening_time", sa.String(length=5), nullable=False, server_default="21:30"),
        sa.Column("weekly_review_time", sa.String(length=20), nullable=False, server_default="Sunday 18:00"),
        sa.Column("weekly_review_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "inbox_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("file_id", sa.String(length=512)),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("priority", sa.Integer()),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "task_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id"), unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reminder_at", sa.DateTime(timezone=True)),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("deadline", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "goal_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("goals.id"), index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "goal_checkins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("goals.id"), index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mood_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("energy", sa.Integer(), nullable=False),
        sa.Column("stress", sa.Integer(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("habit_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "habit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("habit_id", sa.Integer(), sa.ForeignKey("habits.id"), index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Integer()),
        sa.Column("event_type", sa.String(length=32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("habit_id", "log_date", "event_type", name="uq_habit_day_event"),
    )

    op.create_table(
        "habit_protocol_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("log_id", sa.Integer(), sa.ForeignKey("habit_logs.id"), index=True),
        sa.Column("helped", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "schedule_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("pattern", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("work_start", sa.String(length=5), nullable=False, server_default="10:00"),
        sa.Column("work_end", sa.String(length=5), nullable=False, server_default="19:00"),
    )

    op.create_table(
        "schedule_exceptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text()),
    )

    op.create_table(
        "apple_health_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("import_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "apple_health_raw_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("import_id", sa.String(length=64), index=True, nullable=False),
        sa.Column("source", sa.String(length=255)),
        sa.Column("record_type", sa.String(length=255), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.String(length=255)),
        sa.Column("unit", sa.String(length=64)),
        sa.Column("raw_json", postgresql.JSONB(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "apple_health_daily_aggregates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("steps", sa.Integer()),
        sa.Column("distance", sa.Float()),
        sa.Column("active_energy", sa.Float()),
        sa.Column("sleep_duration", sa.Float()),
        sa.Column("avg_hr", sa.Float()),
        sa.Column("min_hr", sa.Float()),
        sa.Column("max_hr", sa.Float()),
        sa.UniqueConstraint("user_id", "date", name="uq_health_day"),
    )

    op.create_table(
        "export_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("export_events")
    op.drop_table("apple_health_daily_aggregates")
    op.drop_table("apple_health_raw_records")
    op.drop_table("apple_health_imports")
    op.drop_table("schedule_exceptions")
    op.drop_table("schedule_templates")
    op.drop_table("habit_protocol_results")
    op.drop_table("habit_logs")
    op.drop_table("habits")
    op.drop_table("mood_entries")
    op.drop_table("goal_checkins")
    op.drop_table("goal_milestones")
    op.drop_table("goals")
    op.drop_table("task_reminders")
    op.drop_table("tasks")
    op.drop_table("inbox_items")
    op.drop_table("user_settings")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
