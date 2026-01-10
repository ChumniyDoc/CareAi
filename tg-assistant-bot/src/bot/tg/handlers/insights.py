from __future__ import annotations

import datetime as dt

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_settings
from bot.db import repo
from bot.llm.agent import run_llm
from bot.llm.approval import execute_if_approved
from bot.llm.client import OllamaClient
from bot.llm.parser import Proposal
from bot.llm.tools import execute_tool

router = Router()


def _proposal_keyboard(action_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"llm:approve:{action_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"llm:decline:{action_id}"),
            ]
        ]
    )


def _format_proposals(proposals: list[Proposal]) -> str:
    lines = []
    for idx, proposal in enumerate(proposals, start=1):
        reason = f" — {proposal.reason}" if proposal.reason else ""
        lines.append(f"{idx}) {proposal.tool}{reason}")
    return "\n".join(lines)


@router.message(Command("insights"))
async def insights(message: Message, session: AsyncSession) -> None:
    settings = load_settings()
    if not settings.llm_enabled:
        await message.answer("LLM отключен. Включи LLM_ENABLED=true в .env")
        return
    user = await repo.get_or_create_user(session, message.from_user.id)
    client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_output_tokens,
    )
    result = await run_llm(session, client, user.id, "Сделай краткие инсайты", settings.llm_context_days)
    if result.response:
        await message.answer(result.response)
    if result.proposals:
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
                f"Предложение:\n{_format_proposals([proposal])}",
                reply_markup=_proposal_keyboard(action.id),
            )
        return
    if not result.response:
        await message.answer("Готово.")


@router.callback_query(F.data.startswith("llm:approve:"))
async def approve_llm_action(callback: CallbackQuery, session: AsyncSession) -> None:
    action_id = int(callback.data.split(":")[-1])
    action = await repo.get_pending_action(session, action_id)
    if not action or action.user_id != callback.from_user.id:
        await callback.answer("Не найдено")
        return
    if action.status != "pending":
        await callback.answer("Уже обработано")
        return
    await repo.update_pending_action_status(session, action, "approved")

    async def _executor(pending_action):
        return await execute_tool(session, pending_action.user_id, pending_action.tool_name, pending_action.tool_args_json)

    executed, result_text = await execute_if_approved(action, _executor)
    await session.commit()
    if executed:
        await callback.message.answer(result_text or "Готово.")
    await callback.answer("Готово")


@router.callback_query(F.data.startswith("llm:decline:"))
async def decline_llm_action(callback: CallbackQuery, session: AsyncSession) -> None:
    action_id = int(callback.data.split(":")[-1])
    action = await repo.get_pending_action(session, action_id)
    if not action or action.user_id != callback.from_user.id:
        await callback.answer("Не найдено")
        return
    await repo.update_pending_action_status(session, action, "declined")
    await session.commit()
    await callback.answer("Отклонено")
