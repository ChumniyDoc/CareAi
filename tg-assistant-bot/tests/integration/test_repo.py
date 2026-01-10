import datetime as dt

from bot.db import models, repo


async def test_create_task(db_session):
    user = await repo.get_or_create_user(db_session, 123)
    task = await repo.create_task(db_session, user.id, "Test", None)
    assert task.id is not None


async def test_habit_log(db_session):
    user = await repo.get_or_create_user(db_session, 1234)
    habit = await repo.create_habit(db_session, user.id, "Test Habit", "checkbox")
    log = await repo.log_habit(db_session, user.id, habit.id, dt.date.today(), 1, None)
    assert log.id is not None


async def test_health_records(db_session):
    user = await repo.get_or_create_user(db_session, 999)
    await repo.store_health_import(db_session, user.id, "import123")
    record = models.AppleHealthRawRecord(
        user_id=user.id,
        import_id="import123",
        source="source",
        record_type="type",
        start_at=dt.datetime.now(dt.timezone.utc),
        end_at=dt.datetime.now(dt.timezone.utc),
        value="1",
        unit="unit",
        raw_json={},
    )
    await repo.store_health_raw_records(db_session, [record])
    assert record.id is not None
