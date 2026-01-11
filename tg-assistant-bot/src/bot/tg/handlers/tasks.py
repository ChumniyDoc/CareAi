from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import repo
from bot.services.tasks import parse_task_text

router = Router()

STATE_AWAIT_TASK = "awaiting_task_text"


class DbStateFilter:
    def __init__(self, state_name: str) -> None:
        self.state_name = state_name

    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        user = await repo.get_or_create_user(session, message.from_user.id)
        state = await repo.get_user_state(session, user.id)
        return state is not None and state.state == self.state_name


def _strip_command_prefix(text: str, command: str) -> str:
    lowered = text.lower()
    if lowered.startswith(f"/{command}"):
        return text[len(f"/{command}") :].strip()
    if lowered.startswith(f"{command} "):
        return text[len(command) :].strip()
    return text


@router.message(Command("add"))
async def add_task(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    text = _strip_command_prefix(message.text, "add")
    if not text:
        user = await repo.get_or_create_user(session, message.from_user.id)
        await repo.set_user_state(session, user.id, STATE_AWAIT_TASK)
        await session.commit()
        await message.answer("Укажи текст задачи: /add купить молоко")
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    settings = load_settings()
    title, due_at = parse_task_text(text, settings.tz)
    task = await repo.create_task(session, user.id, title, due_at)
    await repo.add_task_reminder(session, task)
    await repo.clear_user_state(session, user.id)
    await session.commit()
    await message.answer(f"Задача #{task.id} добавлена.")


@router.message(DbStateFilter(STATE_AWAIT_TASK))
async def add_task_followup(message: Message, session: AsyncSession) -> None:
    text = message.text or ""
    user = await repo.get_or_create_user(session, message.from_user.id)
    settings = load_settings()
    title, due_at = parse_task_text(text, settings.tz)
    task = await repo.create_task(session, user.id, title, due_at)
    await repo.add_task_reminder(session, task)
    await repo.clear_user_state(session, user.id)
    await session.commit()
    await message.answer(f"Задача #{task.id} добавлена.")


@router.message(F.text.regexp(r"(?i)^add(\\s|$)"))
async def add_task_alias(message: Message, session: AsyncSession) -> None:
    if not message.text:
        return
    text = _strip_command_prefix(message.text, "add")
    if not text:
        user = await repo.get_or_create_user(session, message.from_user.id)
        await repo.set_user_state(session, user.id, STATE_AWAIT_TASK)
        await session.commit()
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
