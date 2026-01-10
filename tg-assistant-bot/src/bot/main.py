from __future__ import annotations

import asyncio
import datetime as dt
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, Update

from bot.config import load_settings
from bot.db import repo
from bot.db.session import create_engine, create_session_factory
from bot.jobs.scheduler import SchedulerService
from bot.llm.client import OllamaClient
from bot.logging import setup_logging
from bot.status import BOT_STATUS
from bot.tg.router import router
from bot.web.app import create_app

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
            BOT_STATUS.last_update_at = dt.datetime.now(dt.timezone.utc)
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


class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Handler error")
            message: Message | None = getattr(event, "message", None)
            if message:
                await message.answer("Произошла ошибка. Я записал детали. Попробуй ещё раз.")
            return None


def build_dispatcher(session_factory) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(DbSessionMiddleware(session_factory))
    dispatcher.update.middleware(InboxMiddleware())
    dispatcher.update.middleware(ErrorHandlingMiddleware())
    dispatcher.include_router(router)
    return dispatcher


async def main() -> None:
    setup_logging()
    settings = load_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    scheduler = SchedulerService(settings.tz)
    scheduler.start()

    bot = Bot(token=settings.resolve_bot_token())
    dispatcher = build_dispatcher(session_factory)
    BOT_STATUS.polling_started = True
    BOT_STATUS.polling_started_at = dt.datetime.now(dt.timezone.utc)

    llm_client = None
    if settings.llm_enabled:
        llm_client = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
        )

    web_app = create_app(
        session_factory=session_factory,
        settings=settings,
        scheduler_running=lambda: scheduler.scheduler.running,
        llm_client=llm_client,
    )
    web_config = uvicorn.Config(web_app, host="0.0.0.0", port=8080, log_level="info")
    web_server = uvicorn.Server(web_config)

    logger.info("Starting bot")
    bot_task = asyncio.create_task(dispatcher.start_polling(bot))
    web_task = asyncio.create_task(web_server.serve())
    done, pending = await asyncio.wait({bot_task, web_task}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    scheduler.shutdown()
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
