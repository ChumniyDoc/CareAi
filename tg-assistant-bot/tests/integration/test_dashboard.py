import datetime as dt
import types

import pytest

from bot.db import models, repo
from bot.tg.handlers import dashboard as dashboard_handler


class FakeMessage:
    def __init__(self, text: str = "/dashboard", user_id: int = 1):
        self.text = text
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message_id = 20
        self.responses = []
        self.photos = 0

    async def answer(self, text: str, **kwargs):
        self.responses.append(text)

    async def answer_photo(self, *args, **kwargs):
        self.photos += 1


@pytest.mark.asyncio
async def test_dashboard_fallback_on_chart_error(db_session, monkeypatch):
    user = await repo.get_or_create_user(db_session, 1)
    db_session.add(
        models.AppleHealthDailyAggregate(
            user_id=user.id,
            date=dt.date.today(),
            steps=100,
        )
    )
    await db_session.commit()

    def _boom(*args, **kwargs):
        raise RuntimeError("chart error")

    monkeypatch.setattr(dashboard_handler, "build_simple_chart", _boom)
    message = FakeMessage()
    await dashboard_handler._dashboard(message, db_session)
    assert message.responses
