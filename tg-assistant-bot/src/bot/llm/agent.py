from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo
from bot.llm.client import OllamaClient
from bot.llm.parser import LlmResult, parse_llm_response


def build_prompt(context: dict, user_text: str) -> str:
    return (
        "Ты помощник бота. Верни JSON строго по схеме: "
        "{\"response\":\"...\",\"proposals\":[{\"tool\":\"...\",\"args\":{},\"reason\":\"...\"}]}. "
        "Никакого markdown. Ответ краткий. "
        f"Контекст: {context}. Запрос пользователя: {user_text}"
    )


async def build_context(session: AsyncSession, user_id: int, days: int) -> dict:
    summary = await repo.get_user_summary(session, user_id)
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    tasks_count = await session.execute(
        select(func.count()).select_from(models.Task).where(models.Task.user_id == user_id)
    )
    moods_count = await session.execute(
        select(func.count()).select_from(models.MoodEntry).where(
            models.MoodEntry.user_id == user_id, models.MoodEntry.created_at >= since
        )
    )
    habits_count = await session.execute(
        select(func.count()).select_from(models.HabitLog).where(
            models.HabitLog.user_id == user_id, models.HabitLog.created_at >= since
        )
    )
    return {
        "summary": summary.summary_text if summary else None,
        "tasks_count": tasks_count.scalar_one(),
        "mood_entries_last_days": moods_count.scalar_one(),
        "habit_logs_last_days": habits_count.scalar_one(),
    }


async def run_llm(
    session: AsyncSession,
    client: OllamaClient,
    user_id: int,
    user_text: str,
    context_days: int,
) -> LlmResult:
    context = await build_context(session, user_id, context_days)
    prompt = build_prompt(context, user_text)
    raw = await client.generate(prompt)
    return parse_llm_response(raw)
