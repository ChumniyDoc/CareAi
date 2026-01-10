from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import repo

router = Router()


@router.message(Command("debug_last_error"))
async def debug_last_error(message: Message, session: AsyncSession) -> None:
    settings = load_settings()
    if not settings.admin_telegram_id or message.from_user.id != settings.admin_telegram_id:
        await message.answer("Команда доступна только админу.")
        return
    error = await repo.get_last_error(session)
    await session.commit()
    if not error:
        await message.answer("Ошибок нет.")
        return
    await message.answer(
        f"ERR-{error.id} {error.module}\n{error.message}\n{(error.stacktrace or '').splitlines()[-1]}"
    )
