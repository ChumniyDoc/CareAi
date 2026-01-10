from __future__ import annotations

import datetime as dt

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import repo

router = Router()


@router.message(Command("goal_add"))
async def goal_add(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    text = message.text.replace("/goal_add", "", 1).strip()
    if not text:
        await message.answer("Формат: /goal_add <название> [дата]")
        return
    parts = text.split(" ")
    deadline = None
    if len(parts) > 1:
        try:
            deadline = dt.date.fromisoformat(parts[-1])
            title = " ".join(parts[:-1])
        except ValueError:
            title = text
    else:
        title = text
    user = await repo.get_or_create_user(session, message.from_user.id)
    goal = await repo.create_goal(session, user.id, title, deadline)
    await session.commit()
    await message.answer(f"Цель #{goal.id} добавлена.")


@router.message(Command("goal_list"))
async def goal_list(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    goals = await repo.list_goals(session, user.id)
    await session.commit()
    if not goals:
        await message.answer("Целей пока нет.")
        return
    lines = [f"#{goal.id} {goal.title} ({goal.deadline or 'без срока'})" for goal in goals]
    await message.answer("Цели:\n" + "\n".join(lines))
