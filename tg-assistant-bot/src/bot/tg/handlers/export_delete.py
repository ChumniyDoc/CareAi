from __future__ import annotations

import csv
import io
import time
import zipfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo

router = Router()

_COOLDOWN: dict[int, float] = {}


def _cooldown_check(user_id: int, seconds: int = 60) -> bool:
    now = time.time()
    last = _COOLDOWN.get(user_id, 0)
    if now - last < seconds:
        return False
    _COOLDOWN[user_id] = now
    return True


@router.message(Command("export"))
async def export_data(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    if not _cooldown_check(user.id):
        await message.answer("Подожди минуту перед следующей выгрузкой.")
        return
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        tasks = (await session.execute(select(models.Task).where(models.Task.user_id == user.id))).scalars()
        tasks_list = [
            {
                "id": task.id,
                "title": task.title,
                "due_at": task.due_at.isoformat() if task.due_at else None,
                "status": task.status,
            }
            for task in tasks
        ]
        zf.writestr("tasks.json", str(tasks_list))
        habits = (await session.execute(select(models.Habit).where(models.Habit.user_id == user.id))).scalars()
        habits_list = [{"id": habit.id, "name": habit.name, "type": habit.habit_type} for habit in habits]
        zf.writestr("habits.json", str(habits_list))
        mood_entries = (
            await session.execute(select(models.MoodEntry).where(models.MoodEntry.user_id == user.id))
        ).scalars()
        mood_rows = list(mood_entries)
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["id", "mood", "energy", "stress", "sleep", "note", "created_at"])
        for entry in mood_rows:
            writer.writerow(
                [
                    entry.id,
                    entry.mood,
                    entry.energy,
                    entry.stress,
                    entry.sleep_hours,
                    entry.note,
                    entry.created_at.isoformat(),
                ]
            )
        zf.writestr("mood.csv", csv_buffer.getvalue())
    await session.commit()
    zip_buffer.seek(0)
    await message.answer_document(BufferedInputFile(zip_buffer.read(), filename="export.zip"))


@router.message(Command("delete_data"))
async def delete_data(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    if not _cooldown_check(user.id):
        await message.answer("Подожди минуту перед следующим удалением.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Подтверждаю", callback_data="delete:confirm")]]
    )
    await message.answer("Удалить все данные?", reply_markup=keyboard)


@router.callback_query(F.data == "delete:confirm")
async def delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, callback.from_user.id)
    for model in (
        models.Task,
        models.TaskReminder,
        models.Goal,
        models.GoalMilestone,
        models.GoalCheckIn,
        models.MoodEntry,
        models.Habit,
        models.HabitLog,
        models.HabitProtocolResult,
        models.AppleHealthDailyAggregate,
        models.AppleHealthRawRecord,
        models.AppleHealthImport,
    ):
        await session.execute(model.__table__.delete().where(model.user_id == user.id))
    await session.commit()
    await callback.message.answer("Все данные удалены.")
    await callback.answer()
