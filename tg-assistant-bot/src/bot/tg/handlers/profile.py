from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import repo

router = Router()


class ProfileStates(StatesGroup):
    name = State()
    height = State()
    weight = State()


async def start_profile_wizard(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileStates.name)
    await message.answer("Как тебя зовут?")


@router.message(Command("profile"))
async def profile_show(message: Message, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(session, message.from_user.id)
    profile = await repo.get_user_profile(session, user.id)
    await session.commit()
    if not profile:
        await message.answer("Профиль не заполнен. Используй /profile_edit.")
        return
    await message.answer(
        "Профиль:\n"
        f"Имя: {profile.name}\n"
        f"Рост: {profile.height_cm or '—'}\n"
        f"Вес: {profile.weight_kg or '—'}\n"
        f"Часовой пояс: {profile.timezone}"
    )


@router.message(Command("profile_edit"))
async def profile_edit(message: Message, state: FSMContext) -> None:
    await start_profile_wizard(message, state)


@router.message(ProfileStates.name, F.text.regexp(r"^(?!/).+"))
async def profile_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(ProfileStates.height)
    await message.answer("Рост в см? (или /skip)")


@router.message(ProfileStates.height, Command("skip"))
async def profile_height_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(height_cm=None)
    await state.set_state(ProfileStates.weight)
    await message.answer("Вес в кг? (или /skip)")


@router.message(ProfileStates.height, F.text.regexp(r"^(?!/).+"))
async def profile_height(message: Message, state: FSMContext) -> None:
    if message.text and message.text.isdigit():
        await state.update_data(height_cm=int(message.text))
        await state.set_state(ProfileStates.weight)
        await message.answer("Вес в кг? (или /skip)")
        return
    await message.answer("Введите число или /skip")


@router.message(ProfileStates.weight, Command("skip"))
async def profile_weight_skip(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _finalize_profile(message, state, session, None)


@router.message(ProfileStates.weight, F.text.regexp(r"^(?!/).+"))
async def profile_weight(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        weight_kg = float(message.text)
    except (TypeError, ValueError):
        await message.answer("Введите число или /skip")
        return
    await _finalize_profile(message, state, session, weight_kg)


async def _finalize_profile(
    message: Message, state: FSMContext, session: AsyncSession, weight_kg: float | None
) -> None:
    data = await state.get_data()
    user = await repo.get_or_create_user(session, message.from_user.id)
    await repo.upsert_user_profile(
        session,
        user_id=user.id,
        name=str(data.get("name")),
        height_cm=data.get("height_cm"),
        weight_kg=weight_kg,
        timezone="Asia/Almaty",
    )
    await session.commit()
    await state.clear()
    await message.answer("Профиль сохранен. Можно пользоваться ботом.")
