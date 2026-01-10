from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import repo
from bot.services.inbox import classify_message
from bot.services.tasks import parse_task_text

router = Router()


@router.message(Command("add"))
async def add_task(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    text = message.text.replace("/add", "", 1).strip()
    if not text:
        await message.answer("Укажи текст задачи: /add купить молоко")
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    settings = load_settings()
    title, due_at = parse_task_text(text, settings.tz)
    task = await repo.create_task(session, user.id, title, due_at)
    await repo.add_task_reminder(session, task)
    await session.commit()
    await message.answer(f"Задача #{task.id} добавлена.")


@router.message(Command("tasks"))
async def list_tasks(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    tasks = await repo.list_open_tasks(session, user.id)
    await session.commit()
    if not tasks:
        await message.answer("Открытых задач нет.")
        return
    lines = [f"#{task.id} {task.title} ({task.due_at or 'без срока'})" for task in tasks]
    await message.answer("Список задач:\n" + "\n".join(lines))


@router.message(Command("done"))
async def done_task(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /done <id>")
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    ok = await repo.mark_task_done(session, user.id, int(parts[1]))
    await session.commit()
    if ok:
        await message.answer("Отмечено как выполнено.")
    else:
        await message.answer("Задача не найдена.")


@router.message(F.text)
async def natural_task(message: Message, session: AsyncSession) -> None:
    if message.text and message.text.startswith("/"):
        return
    text = message.text or ""
    user = await repo.get_or_create_user(session, message.from_user.id)
    classification = classify_message(text)
    if classification.kind == "task":
        settings = load_settings()
        title, due_at = parse_task_text(text, settings.tz)
        task = await repo.create_task(session, user.id, title, due_at)
        await repo.add_task_reminder(session, task)
        await session.commit()
        await message.answer(f"Создал задачу #{task.id} из сообщения.")
        return
    if classification.kind == "mood":
        await message.answer("Похоже на запись настроения. Вызови /mood.")
        return
    if classification.kind == "habit":
        await message.answer("Похоже на привычку. Вызови /habit_log.")
        return
    await message.answer("Сохранил заметку. Позже предложу разобрать.")
