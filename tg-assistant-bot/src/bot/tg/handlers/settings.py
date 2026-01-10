from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo

router = Router()


@router.message(Command("settings"))
async def settings_show(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    result = await session.execute(select(models.UserSettings).where(models.UserSettings.user_id == user.id))
    settings = result.scalar_one()
    await session.commit()
    await message.answer(
        "Настройки:\n"
        f"Утро: {settings.morning_time}\n"
        f"Вечер: {settings.evening_time}\n"
        f"Еженедельный обзор: {settings.weekly_review_time} ({'вкл' if settings.weekly_review_enabled else 'выкл'})\n"
        "Обновить: /settings_set morning=09:00 evening=21:30 weekly=Sunday18:00 review=on"
    )


@router.message(Command("settings_set"))
async def settings_set(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    result = await session.execute(select(models.UserSettings).where(models.UserSettings.user_id == user.id))
    settings = result.scalar_one()
    parts = message.text.replace("/settings_set", "", 1).strip().split()
    for part in parts:
        if part.startswith("morning="):
            settings.morning_time = part.split("=", 1)[1]
        if part.startswith("evening="):
            settings.evening_time = part.split("=", 1)[1]
        if part.startswith("weekly="):
            settings.weekly_review_time = part.split("=", 1)[1].replace(" ", "")
        if part.startswith("review="):
            settings.weekly_review_enabled = part.split("=", 1)[1].lower() == "on"
    await session.commit()
    await message.answer("Настройки обновлены.")
