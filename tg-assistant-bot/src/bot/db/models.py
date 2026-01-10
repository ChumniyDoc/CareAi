from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base


class InboxStatus(str, Enum):
    new = "new"
    processed = "processed"


class TaskStatus(str, Enum):
    open = "open"
    done = "done"


class HabitType(str, Enum):
    checkbox = "checkbox"
    counter = "counter"
    scheduled = "scheduled"
    system = "system"


class HabitEventType(str, Enum):
    craving = "craving"
    relapse = "relapse"
    portion = "portion"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    morning_time: Mapped[str] = mapped_column(String(5), default="09:00")
    evening_time: Mapped[str] = mapped_column(String(5), default="21:30")
    weekly_review_time: Mapped[str] = mapped_column(String(20), default="Sunday 18:00")
    weekly_review_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class UserState(Base):
    __tablename__ = "user_states"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    state: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InboxItem(Base):
    __tablename__ = "inbox_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_id: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(32))
    raw_text: Mapped[str | None] = mapped_column(Text)
    file_id: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default=InboxStatus.new.value)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default=TaskStatus.open.value)
    priority: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list[str] | None] = mapped_column(JSONB)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskReminder(Base):
    __tablename__ = "task_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reminder_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    sent: Mapped[bool] = mapped_column(Boolean, default=False)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    deadline: Mapped[dt.date | None] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GoalMilestone(Base):
    __tablename__ = "goal_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GoalCheckIn(Base):
    __tablename__ = "goal_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mood: Mapped[int] = mapped_column(Integer)
    energy: Mapped[int] = mapped_column(Integer)
    stress: Mapped[int] = mapped_column(Integer)
    sleep_hours: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    habit_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[dt.date] = mapped_column(Date)
    value: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("habit_id", "log_date", "event_type", name="uq_habit_day_event"),)


class HabitProtocolResult(Base):
    __tablename__ = "habit_protocol_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_id: Mapped[int] = mapped_column(ForeignKey("habit_logs.id"), index=True)
    helped: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    month: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    pattern: Mapped[str] = mapped_column(String(32))
    start_date: Mapped[dt.date] = mapped_column(Date)
    work_start: Mapped[str] = mapped_column(String(5), default="10:00")
    work_end: Mapped[str] = mapped_column(String(5), default="19:00")


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[dt.date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)


class AppleHealthImport(Base):
    __tablename__ = "apple_health_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    import_id: Mapped[str] = mapped_column(String(64), unique=True)
    imported_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppleHealthRawRecord(Base):
    __tablename__ = "apple_health_raw_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    import_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str | None] = mapped_column(String(255))
    record_type: Mapped[str] = mapped_column(String(255))
    start_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(64))
    raw_json: Mapped[dict] = mapped_column(JSONB)
    imported_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppleHealthDailyAggregate(Base):
    __tablename__ = "apple_health_daily_aggregates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date)
    steps: Mapped[int | None] = mapped_column(Integer)
    distance: Mapped[float | None] = mapped_column(Float)
    active_energy: Mapped[float | None] = mapped_column(Float)
    sleep_duration: Mapped[float | None] = mapped_column(Float)
    avg_hr: Mapped[float | None] = mapped_column(Float)
    min_hr: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[float | None] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_health_day"),)


class ExportEvent(Base):
    __tablename__ = "export_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserProfileSummary(Base):
    __tablename__ = "user_profile_summaries"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    summary_text: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LlmInteractionLog(Base):
    __tablename__ = "llm_interaction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_text: Mapped[str] = mapped_column(Text)
    assistant_text: Mapped[str] = mapped_column(Text)
    tool_calls_json: Mapped[list[dict] | None] = mapped_column(JSONB)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    tool_args_json: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
