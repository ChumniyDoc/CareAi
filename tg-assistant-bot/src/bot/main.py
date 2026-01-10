from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, Update

from bot.config import load_settings
from bot.db import repo
from bot.db.session import create_engine, create_session_factory
from bot.logging import setup_logging
from bot.tg.router import router

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __call__(self, handler, event: Update, data: dict):
        async with self.session_factory() as session:
            data["session"] = session
            result = await handler(event, data)
            await session.commit()
            return result


class InboxMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        message: Message | None = getattr(event, "message", None)
        if message and message.from_user:
            session = data.get("session")
            if session:
                user = await repo.get_or_create_user(session, message.from_user.id)
                kind = "text"
                raw_text = message.text
                file_id = None
                if message.voice:
                    kind = "voice"
                    file_id = message.voice.file_id
                if message.document:
                    kind = "document"
                    file_id = message.document.file_id
                await repo.add_inbox_item(
                    session,
                    user_id=user.id,
                    message_id=message.message_id,
                    kind=kind,
                    raw_text=raw_text,
                    file_id=file_id,
                )
        return await handler(event, data)


def build_dispatcher(session_factory) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.update.middleware(DbSessionMiddleware(session_factory))
    dispatcher.update.middleware(InboxMiddleware())
    dispatcher.include_router(router)
    return dispatcher


async def main() -> None:
    setup_logging()
    settings = load_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    bot = Bot(token=settings.resolve_bot_token())
    dispatcher = build_dispatcher(session_factory)

    logger.info("Starting bot")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
