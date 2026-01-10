from __future__ import annotations

import datetime as dt
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo
from bot.services.dashboard import build_simple_chart

router = Router()
logger = logging.getLogger(__name__)


async def _dashboard(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    since = dt.date.today() - dt.timedelta(days=13)
    result = await session.execute(
        select(models.AppleHealthDailyAggregate)
        .where(models.AppleHealthDailyAggregate.user_id == user.id)
        .where(models.AppleHealthDailyAggregate.date >= since)
        .order_by(models.AppleHealthDailyAggregate.date)
    )
    rows = result.scalars().all()
    await session.commit()
    if not rows:
        await message.answer("Дашборд: пока нет данных. Добавь привычки или импортируй здоровье.")
        return
    labels = [row.date.strftime("%m-%d") for row in rows]
    steps = [row.steps or 0 for row in rows]
    await message.answer(
        f"Дашборд за 14 дней: записей {len(rows)}. Средние шаги: {sum(steps) // max(len(steps), 1)}."
    )
    try:
        chart = build_simple_chart("Шаги", labels, steps)
        await message.answer_photo(BufferedInputFile(chart, filename="steps.png"))
    except Exception:
        logger.exception("Failed to build dashboard chart")


@router.message(Command("dashboard"))
async def dashboard(message: Message, session: AsyncSession) -> None:
    await _dashboard(message, session)


@router.message(F.text.regexp(r"^(?i)dashboard(\\s|$)"))
async def dashboard_alias(message: Message, session: AsyncSession) -> None:
    await _dashboard(message, session)
