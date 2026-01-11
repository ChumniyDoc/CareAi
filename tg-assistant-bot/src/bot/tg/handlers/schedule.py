from __future__ import annotations

import datetime as dt

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo
from bot.services.schedule import is_workday, month_calendar

router = Router()


@router.message(Command("schedule"))
async def schedule_menu(message: Message) -> None:
    await message.answer(
        "Команды расписания:\n"
        "/schedule_set <pattern 5/2> <YYYY-MM-DD>\n"
        "/schedule_show <YYYY-MM>"
    )


@router.message(Command("schedule_set"))
async def schedule_set(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: /schedule_set 5/2 2024-05-01")
        return
    pattern = parts[1]
    start_date = dt.date.fromisoformat(parts[2])
    month = start_date.strftime("%Y-%m")
    user = await repo.get_or_create_user(session, message.from_user.id)
    template = models.ScheduleTemplate(
        user_id=user.id,
        month=month,
        pattern=pattern,
        start_date=start_date,
    )
    session.add(template)
    await session.commit()
    await message.answer("Шаблон расписания сохранен.")


@router.message(Command("schedule_show"))
async def schedule_show(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: /schedule_show YYYY-MM")
        return
    year, month = map(int, parts[1].split("-"))
    user = await repo.get_or_create_user(session, message.from_user.id)
    result = await session.execute(
        models.ScheduleTemplate.__table__.select().where(
            models.ScheduleTemplate.user_id == user.id,
            models.ScheduleTemplate.month == parts[1],
        )
    )
    row = result.first()
    if not row:
        await message.answer("Нет шаблона на этот месяц.")
        return
    template = models.ScheduleTemplate(**row._mapping)
    calendar_grid = month_calendar(year, month)
    lines = []
    for week in calendar_grid:
        line = []
        for day in week:
            if day == 0:
                line.append("  ")
                continue
            date = dt.date(year, month, day)
            line.append("Р" if is_workday(date, template.start_date, template.pattern) else "В")
        lines.append(" ".join(line))
    await message.answer("Календарь (Р=работа, В=выходной):\n" + "\n".join(lines))
