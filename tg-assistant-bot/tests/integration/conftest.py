import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.session import create_engine, create_session_factory


@pytest.fixture(scope="session")
def database_url():
    return os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tg_assistant")


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(database_url):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


@pytest.fixture()
async def db_session(database_url):
    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        yield session
    await engine.dispose()
