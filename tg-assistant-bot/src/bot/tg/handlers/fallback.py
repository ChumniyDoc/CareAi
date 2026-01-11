from __future__ import annotations

import datetime as dt

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import repo
from bot.llm.agent import run_intent
from bot.llm.client import OllamaClient
from bot.llm.parser import IntentResult, Proposal
from bot.services.inbox import classify_message

router = Router()


def _note_keyboard(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сохранить", callback_data=f"note:save:{message_id}"),
                InlineKeyboardButton(text="❌ Не надо", callback_data=f"note:skip:{message_id}"),
            ]
        ]
    )


def _proposal_keyboard(action_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"llm:approve:{action_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"llm:decline:{action_id}"),
            ]
        ]
    )


def _format_proposal(proposal: Proposal) -> str:
    reason = f" — {proposal.reason}" if proposal.reason else ""
    return f"{proposal.tool}{reason}"


async def _handle_intent_result(
    message: Message, session: AsyncSession, result: IntentResult
) -> None:
    if result.reply:
        await message.answer(result.reply)
    if result.proposals:
        user = await repo.get_or_create_user(session, message.from_user.id)
        for proposal in result.proposals:
            action = await repo.create_pending_action(
                session,
                user.id,
                proposal.tool,
                proposal.args,
                proposal.reason,
                dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1),
            )
            await session.commit()
            await message.answer(
                f"Предложение:\n{_format_proposal(proposal)}",
                reply_markup=_proposal_keyboard(action.id),
            )


@router.message(F.text)
async def fallback(message: Message, session: AsyncSession) -> None:
    if message.text and message.text.startswith("/"):
        return
    text = message.text or ""
    classification = classify_message(text)
    if classification.kind == "task":
        await message.answer("Похоже на задачу. Напиши /add <текст>.")
        return
    if classification.kind == "mood":
        await message.answer("Похоже на запись настроения. Вызови /mood.")
        return
    if classification.kind == "habit":
        await message.answer("Похоже на привычку. Вызови /habit_log.")
        return

    settings = load_settings()
    if settings.llm_enabled:
        client = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
        )
        user = await repo.get_or_create_user(session, message.from_user.id)
        try:
            result = await run_intent(session, client, user.id, text, settings.llm_context_days)
        except Exception:
            await message.answer(
                "LLM недоступна. Сохранить как заметку?",
                reply_markup=_note_keyboard(message.message_id),
            )
            return
        await _handle_intent_result(message, session, result)
        if not result.valid_json:
            await message.answer("Сохранить как заметку?", reply_markup=_note_keyboard(message.message_id))
            return
        if result.intent in {"note_store", "unknown"} or not result.reply:
            await message.answer("Сохранить как заметку?", reply_markup=_note_keyboard(message.message_id))
        return

    await message.answer("Сохранить как заметку?", reply_markup=_note_keyboard(message.message_id))


@router.callback_query(F.data.startswith("note:save:"))
async def note_save(callback: CallbackQuery, session: AsyncSession) -> None:
    message_id = int(callback.data.split(":")[-1])
    user = await repo.get_or_create_user(session, callback.from_user.id)
    item = await repo.get_inbox_item_by_message(session, user.id, message_id)
    if item:
        await repo.update_inbox_status(session, item, "processed")
        await session.commit()
    await callback.message.answer("Сохранил заметку.")
    await callback.answer()


@router.callback_query(F.data.startswith("note:skip:"))
async def note_skip(callback: CallbackQuery) -> None:
    await callback.message.answer("Ок, не сохраняю.")
    await callback.answer()
