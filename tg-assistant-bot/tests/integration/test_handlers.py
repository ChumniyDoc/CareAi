import types

import pytest

from bot.tg.handlers.tasks import add_task


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
