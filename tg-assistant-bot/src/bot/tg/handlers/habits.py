from __future__ import annotations

import datetime as dt

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import models, repo
from bot.services.habits import handle_alcohol_portion, normalize_trigger

router = Router()


async def ensure_system_habits(session: AsyncSession, user_id: int) -> dict[str, models.Habit]:
    habits = await repo.list_habits(session, user_id)
    habit_map = {habit.name: habit for habit in habits}
    for name in ("Никотин", "Алкоголь"):
        if name not in habit_map:
            habit = await repo.create_habit(session, user_id, name, models.HabitType.system.value)
            habit_map[name] = habit
    return habit_map


@router.message(Command("habit_create"))
async def habit_create(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Формат: /habit_create <checkbox|counter|scheduled> <название>")
        return
    habit_type, name = parts[1], parts[2]
    user = await repo.get_or_create_user(session, message.from_user.id)
    habit = await repo.create_habit(session, user.id, name, habit_type)
    await session.commit()
    await message.answer(f"Привычка #{habit.id} создана.")


@router.message(Command("habit_log"))
async def habit_log(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    habits = await repo.list_habits(session, user.id)
    await session.commit()
    if not habits:
        await message.answer("Пока нет привычек. Используй /habit_create.")
        return
    buttons = [InlineKeyboardButton(text=habit.name, callback_data=f"habit:{habit.id}") for habit in habits]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer("Выбери привычку:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("habit:"))
async def habit_log_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    habit_id = int(callback.data.split(":")[1])
    user = await repo.get_or_create_user(session, callback.from_user.id)
    log = await repo.log_habit(session, user.id, habit_id, dt.date.today(), 1, None)
    await session.commit()
    await callback.message.answer(f"Лог сохранен #{log.id}.")
    await callback.answer()


@router.message(F.text)
async def habit_trigger(message: Message, session: AsyncSession) -> None:
    if not message.text or message.text.startswith("/"):
        return
    if not normalize_trigger(message.text):
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    habit_map = await ensure_system_habits(session, user.id)
    nicotine = habit_map["Никотин"]
    log = await repo.log_habit(session, user.id, nicotine.id, dt.date.today(), None, models.HabitEventType.craving.value)
    await session.commit()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="прошло", callback_data=f"protocol:{log.id}:1"),
                InlineKeyboardButton(text="не прошло", callback_data=f"protocol:{log.id}:0"),
            ]
        ]
    )
    await message.answer(
        "Протокол 2 минуты:\n"
        "1) 4-7-8 дыхание (4 вдох, 7 задержка, 8 выдох)\n"
        "2) Отслеживай волну тяги, она проходит\n"
        "3) Выбери замену: вода, 10 приседаний, короткая прогулка",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("protocol:"))
async def protocol_result(callback: CallbackQuery, session: AsyncSession) -> None:
    _, log_id, helped = callback.data.split(":")
    user = await repo.get_or_create_user(session, callback.from_user.id)
    session.add(models.HabitProtocolResult(user_id=user.id, log_id=int(log_id), helped=bool(int(helped))))
    await session.commit()
    await callback.message.answer("Сохранил ответ, спасибо!")
    await callback.answer()


@router.message(Command("alcohol"))
async def log_alcohol(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /alcohol <кол-во порций>")
        return
    count = int(parts[1])
    user = await repo.get_or_create_user(session, message.from_user.id)
    habit_map = await ensure_system_habits(session, user.id)
    alcohol = habit_map["Алкоголь"]
    result = handle_alcohol_portion(count)
    await repo.log_habit(
        session,
        user.id,
        alcohol.id,
        dt.date.today(),
        count,
        models.HabitEventType.portion.value,
    )
    if result.relapse:
        await repo.log_habit(
            session,
            user.id,
            alcohol.id,
            dt.date.today(),
            None,
            models.HabitEventType.relapse.value,
        )
    await session.commit()
    await message.answer("Записал лог алкоголя.")
