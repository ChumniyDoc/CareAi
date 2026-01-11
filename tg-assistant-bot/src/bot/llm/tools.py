from __future__ import annotations

import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo
from bot.services.tasks import parse_task_text


async def execute_tool(session: AsyncSession, user_id: int, tool_name: str, args: dict) -> str:
    if tool_name == "create_task":
        title = str(args.get("title") or "").strip()
        due_at = None
        if args.get("due_at"):
            due_at = dt.datetime.fromisoformat(args["due_at"])
        if not title:
            raise ValueError("empty title")
        task = await repo.create_task(session, user_id, title, due_at)
        await repo.add_task_reminder(session, task)
        return f"Создал задачу #{task.id}."
    if tool_name == "log_nicotine":
        event = args.get("event", "craving")
        habit = await _get_or_create_system_habit(session, user_id, "Никотин")
        await repo.log_habit(session, user_id, habit.id, dt.date.today(), None, event)
        return "Записал событие по никотину."
    if tool_name == "log_alcohol":
        habit = await _get_or_create_system_habit(session, user_id, "Алкоголь")
        portions = int(args.get("portions", 0))
        await repo.log_habit(session, user_id, habit.id, dt.date.today(), portions, "portion")
        return "Записал алкоголь."
    if tool_name == "add_goal":
        title = str(args.get("title") or "").strip()
        if not title:
            raise ValueError("empty title")
        await repo.create_goal(session, user_id, title, None)
        return "Цель добавлена."
    if tool_name == "add_mood_entry":
        await repo.create_mood_entry(
            session,
            user_id,
            int(args.get("mood", 5)),
            int(args.get("energy", 5)),
            int(args.get("stress", 5)),
            float(args.get("sleep_hours", 7)),
            args.get("note"),
        )
        return "Записал настроение."
    if tool_name == "schedule_exception":
        day = dt.date.fromisoformat(args["date"])
        kind = str(args.get("type", "off"))
        session.add(models.ScheduleException(user_id=user_id, day=day, kind=kind, note=None))
        return "Добавил исключение в расписание."
    raise ValueError(f"Unknown tool: {tool_name}")


async def _get_or_create_system_habit(session: AsyncSession, user_id: int, name: str) -> models.Habit:
    habits = await repo.list_habits(session, user_id)
    for habit in habits:
        if habit.name == name:
            return habit
    return await repo.create_habit(session, user_id, name, models.HabitType.system.value)


def format_task_from_text(text: str, tz: str) -> tuple[str, dt.datetime | None]:
    return parse_task_text(text, tz)
