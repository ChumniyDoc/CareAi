from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import repo
from bot.tg.handlers.profile import start_profile_wizard

router = Router()


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    profile = await repo.get_user_profile(session, user.id)
    await session.commit()
    if not profile:
        await start_profile_wizard(message, state)
        return
    await message.answer(
        "Привет! Я твой персональный операционный бот. "
        "Доступные команды: /add, /tasks, /done, /mood, /habit_log, /goal_add, /goal_list, /dashboard, /insights."
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/add <текст> — новая задача\n"
        "/tasks — список задач\n"
        "/done <id> — закрыть задачу\n"
        "/mood — дневник настроения\n"
        "/habit_create — создать привычку\n"
        "/habit_log — лог привычки\n"
        "/goal_add <текст> — цель\n"
        "/profile — профиль\n"
        "/profile_edit — редактировать профиль\n"
        "/dashboard — графики\n"
        "/insights — краткие инсайты\n"
        "/export — выгрузка\n"
        "/delete_data — удалить данные"
    )
