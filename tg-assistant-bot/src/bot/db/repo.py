from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models


async def get_or_create_user(session: AsyncSession, telegram_id: int) -> models.User:
    result = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = models.User(telegram_id=telegram_id)
    session.add(user)
    await session.flush()
    session.add(models.UserSettings(user_id=user.id))
    return user


async def add_inbox_item(
    session: AsyncSession,
    user_id: int,
    message_id: int,
    kind: str,
    raw_text: str | None,
    file_id: str | None,
) -> models.InboxItem:
    item = models.InboxItem(
        user_id=user_id,
        message_id=message_id,
        kind=kind,
        raw_text=raw_text,
        file_id=file_id,
    )
    session.add(item)
    return item


async def create_task(session: AsyncSession, user_id: int, title: str, due_at: dt.datetime | None) -> models.Task:
    task = models.Task(user_id=user_id, title=title, due_at=due_at)
    session.add(task)
    await session.flush()
    return task


async def add_task_reminder(session: AsyncSession, task: models.Task) -> None:
    if task.due_at is None:
        return
    existing = await session.execute(
        select(models.TaskReminder).where(models.TaskReminder.task_id == task.id)
    )
    if existing.scalar_one_or_none():
        return
    session.add(
        models.TaskReminder(task_id=task.id, user_id=task.user_id, reminder_at=task.due_at)
    )


async def list_open_tasks(session: AsyncSession, user_id: int) -> Sequence[models.Task]:
    result = await session.execute(
        select(models.Task)
        .where(models.Task.user_id == user_id, models.Task.status == models.TaskStatus.open.value)
        .order_by(models.Task.due_at.nulls_last())
    )
    return result.scalars().all()


async def mark_task_done(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(models.Task).where(models.Task.user_id == user_id, models.Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        return False
    task.status = models.TaskStatus.done.value
    return True


async def list_goals(session: AsyncSession, user_id: int) -> Sequence[models.Goal]:
    result = await session.execute(select(models.Goal).where(models.Goal.user_id == user_id))
    return result.scalars().all()


async def create_goal(session: AsyncSession, user_id: int, title: str, deadline: dt.date | None) -> models.Goal:
    goal = models.Goal(user_id=user_id, title=title, deadline=deadline)
    session.add(goal)
    await session.flush()
    return goal


async def create_mood_entry(
    session: AsyncSession,
    user_id: int,
    mood: int,
    energy: int,
    stress: int,
    sleep_hours: float,
    note: str | None,
) -> models.MoodEntry:
    entry = models.MoodEntry(
        user_id=user_id,
        mood=mood,
        energy=energy,
        stress=stress,
        sleep_hours=sleep_hours,
        note=note,
    )
    session.add(entry)
    await session.flush()
    return entry


async def list_habits(session: AsyncSession, user_id: int) -> Sequence[models.Habit]:
    result = await session.execute(select(models.Habit).where(models.Habit.user_id == user_id))
    return result.scalars().all()


async def create_habit(session: AsyncSession, user_id: int, name: str, habit_type: str) -> models.Habit:
    habit = models.Habit(user_id=user_id, name=name, habit_type=habit_type)
    session.add(habit)
    await session.flush()
    return habit


async def log_habit(
    session: AsyncSession,
    user_id: int,
    habit_id: int,
    log_date: dt.date,
    value: int | None,
    event_type: str | None,
) -> models.HabitLog:
    log = models.HabitLog(
        user_id=user_id,
        habit_id=habit_id,
        log_date=log_date,
        value=value,
        event_type=event_type,
    )
    session.add(log)
    await session.flush()
    return log


async def store_health_import(session: AsyncSession, user_id: int, import_id: str) -> models.AppleHealthImport:
    record = models.AppleHealthImport(user_id=user_id, import_id=import_id)
    session.add(record)
    await session.flush()
    return record


async def has_health_import(session: AsyncSession, import_id: str) -> bool:
    result = await session.execute(
        select(models.AppleHealthImport).where(models.AppleHealthImport.import_id == import_id)
    )
    return result.scalar_one_or_none() is not None


async def store_health_raw_records(
    session: AsyncSession, records: list[models.AppleHealthRawRecord]
) -> None:
    session.add_all(records)


async def upsert_health_aggregate(session: AsyncSession, aggregate: models.AppleHealthDailyAggregate) -> None:
    result = await session.execute(
        select(models.AppleHealthDailyAggregate).where(
            models.AppleHealthDailyAggregate.user_id == aggregate.user_id,
            models.AppleHealthDailyAggregate.date == aggregate.date,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        for field in (
            "steps",
            "distance",
            "active_energy",
            "sleep_duration",
            "avg_hr",
            "min_hr",
            "max_hr",
        ):
            value = getattr(aggregate, field)
            if value is not None:
                setattr(existing, field, value)
        return
    session.add(aggregate)


async def get_user_summary(session: AsyncSession, user_id: int) -> models.UserProfileSummary | None:
    result = await session.execute(
        select(models.UserProfileSummary).where(models.UserProfileSummary.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_user_summary(session: AsyncSession, user_id: int, summary_text: str) -> None:
    existing = await get_user_summary(session, user_id)
    if existing:
        existing.summary_text = summary_text
        return
    session.add(models.UserProfileSummary(user_id=user_id, summary_text=summary_text))


async def store_llm_interaction(
    session: AsyncSession,
    user_id: int,
    user_text: str,
    assistant_text: str,
    tool_calls: list[dict] | None,
) -> models.LlmInteractionLog:
    record = models.LlmInteractionLog(
        user_id=user_id,
        user_text=user_text,
        assistant_text=assistant_text,
        tool_calls_json=tool_calls,
    )
    session.add(record)
    await session.flush()
    return record


async def create_pending_action(
    session: AsyncSession,
    user_id: int,
    tool_name: str,
    tool_args: dict,
    reason: str | None,
    expires_at: dt.datetime | None,
) -> models.PendingAction:
    record = models.PendingAction(
        user_id=user_id,
        tool_name=tool_name,
        tool_args_json=tool_args,
        reason=reason,
        expires_at=expires_at,
    )
    session.add(record)
    await session.flush()
    return record


async def get_pending_action(session: AsyncSession, action_id: int) -> models.PendingAction | None:
    result = await session.execute(
        select(models.PendingAction).where(models.PendingAction.id == action_id)
    )
    return result.scalar_one_or_none()


async def update_pending_action_status(
    session: AsyncSession, action: models.PendingAction, status: str
) -> None:
    action.status = status
