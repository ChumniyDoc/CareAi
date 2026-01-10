import types

import pytest

from bot.db import repo
from bot.tg.handlers.tasks import add_task, add_task_alias, add_task_followup


class FakeMessage:
    def __init__(self, text: str, user_id: int = 1):
        self.text = text
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message_id = 10
        self.responses = []

    async def answer(self, text: str, **kwargs):
        self.responses.append(text)


@pytest.mark.asyncio
async def test_add_task_handler(db_session):
    message = FakeMessage("/add купить молоко")
    await add_task(message, db_session)
    assert message.responses


@pytest.mark.asyncio
async def test_add_followup_creates_task(db_session):
    message = FakeMessage("/add")
    await add_task(message, db_session)
    followup = FakeMessage("add купить молоко")
    await add_task_followup(followup, db_session)
    user = await repo.get_or_create_user(db_session, followup.from_user.id)
    tasks = await repo.list_open_tasks(db_session, user.id)
    assert tasks


@pytest.mark.asyncio
async def test_add_alias_case_insensitive(db_session):
    message = FakeMessage("AdD Протестировать")
    await add_task_alias(message, db_session)
    user = await repo.get_or_create_user(db_session, message.from_user.id)
    tasks = await repo.list_open_tasks(db_session, user.id)
    assert tasks
