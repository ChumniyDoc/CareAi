from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import repo

router = Router()


class MoodStates(StatesGroup):
    mood = State()
    energy = State()
    stress = State()
    sleep = State()
    note = State()


def _scale_keyboard(prefix: str, max_value: int = 10) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=str(i), callback_data=f"{prefix}:{i}") for i in range(1, max_value + 1)]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


async def _start_mood(message: Message, state: FSMContext) -> None:
    await state.set_state(MoodStates.mood)
    await message.answer("Оцени настроение 1-10:", reply_markup=_scale_keyboard("mood"))


@router.message(Command("mood"))
async def mood_start(message: Message, state: FSMContext) -> None:
    await _start_mood(message, state)


@router.message(F.text.regexp(r"^(?i)mood(\\s|$)"))
async def mood_alias(message: Message, state: FSMContext) -> None:
    await _start_mood(message, state)


@router.callback_query(F.data.startswith("mood:"))
async def mood_pick(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":")[1])
    await state.update_data(mood=value)
    await state.set_state(MoodStates.energy)
    await callback.message.answer("Энергия 1-10:", reply_markup=_scale_keyboard("energy"))
    await callback.answer()


@router.callback_query(F.data.startswith("energy:"))
async def energy_pick(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":")[1])
    await state.update_data(energy=value)
    await state.set_state(MoodStates.stress)
    await callback.message.answer("Стресс 1-10:", reply_markup=_scale_keyboard("stress"))
    await callback.answer()


@router.callback_query(F.data.startswith("stress:"))
async def stress_pick(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":")[1])
    await state.update_data(stress=value)
    await state.set_state(MoodStates.sleep)
    await callback.message.answer("Сон (часы):", reply_markup=_scale_keyboard("sleep", 12))
    await callback.answer()


@router.callback_query(F.data.startswith("sleep:"))
async def sleep_pick(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":")[1])
    await state.update_data(sleep=value)
    await state.set_state(MoodStates.note)
    await callback.message.answer("Добавь заметку или /skip")
    await callback.answer()


@router.message(MoodStates.note)
async def note_pick(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    note = None if message.text == "/skip" else message.text
    user = await repo.get_or_create_user(session, message.from_user.id)
    await repo.create_mood_entry(
        session,
        user.id,
        mood=int(data["mood"]),
        energy=int(data["energy"]),
        stress=int(data["stress"]),
        sleep_hours=float(data["sleep"]),
        note=note,
    )
    await session.commit()
    await message.answer("Сохранил запись настроения.")
    await state.clear()
