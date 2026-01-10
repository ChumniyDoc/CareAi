from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(slots=True)
class BriefingData:
    tasks: list[str]
    next_reminder: str | None
    workday_label: str


@dataclass(slots=True)
class ReflectionData:
    questions: list[str]


def build_morning_briefing(data: BriefingData) -> str:
    tasks_text = "\n".join(f"- {task}" for task in data.tasks) or "Нет задач"
    reminder = data.next_reminder or "нет"
    return (
        "Доброе утро!\n"
        f"Сегодня: {data.workday_label}\n"
        f"Задачи:\n{tasks_text}\n"
        f"Следующее напоминание: {reminder}"
    )


def build_evening_reflection(data: ReflectionData) -> str:
    questions = "\n".join(f"- {question}" for question in data.questions)
    return "Вечерняя рефлексия:\n" + questions


def weekly_review_prompt(items: list[str]) -> str:
    if not items:
        return "На этой неделе нет заметок для разбора."
    lines = "\n".join(f"- {item}" for item in items)
    return "Еженедельный разбор входящих:\n" + lines


def next_weekday(target_weekday: int, now: dt.datetime) -> dt.datetime:
    days_ahead = (target_weekday - now.weekday()) % 7
    return now + dt.timedelta(days=days_ahead)
