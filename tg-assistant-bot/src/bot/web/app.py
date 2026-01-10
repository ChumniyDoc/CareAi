from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import Settings
from bot.llm.client import OllamaClient
from bot.llm.state import LLM_STATUS
from bot.status import BOT_STATUS

security = HTTPBasic()


def _auth_dependency(settings: Settings):
    def verify(credentials: HTTPBasicCredentials = Depends(security)) -> str:
        expected_user = settings.admin_user
        expected_password = settings.admin_password or "admin"
        if not secrets.compare_digest(credentials.username, expected_user) or not secrets.compare_digest(
            credentials.password, expected_password
        ):
            raise HTTPException(status_code=401, detail="Unauthorized")
        return credentials.username

    return verify


def create_app(
    session_factory,
    settings: Settings,
    scheduler_running: callable,
    llm_client: OllamaClient | None,
) -> FastAPI:
    app = FastAPI()
    auth_dependency = _auth_dependency(settings)

    async def get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(session: AsyncSession = Depends(get_session)) -> dict:
        await _check_db(session)
        await _check_migrations(session)
        return {"status": "ok"}

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page(
        request: Request,
        user: str = Depends(auth_dependency),
        session: AsyncSession = Depends(get_session),
    ) -> str:
        stats = await build_stats(session, settings, scheduler_running, llm_client)
        rows_html = "".join(
            f"<tr><td>{name}</td><td>{value}</td></tr>" for name, value in stats["table_counts"].items()
        )
        errors_html = "<br/>".join(stats["recent_errors"]) or "Нет"
        return (
            "<html><body>"
            "<h1>Admin</h1>"
            "<form method='post' action='/admin/selftest'>"
            "<button type='submit'>Run self-test</button>"
            "</form>"
            "<h2>DB</h2>"
            f"<p>Размер БД: {stats['db_size']}</p>"
            "<table border='1'><tr><th>Table</th><th>Rows</th></tr>"
            f"{rows_html}</table>"
            "<h2>Status</h2>"
            f"<p>DB: {stats['status']['db']}</p>"
            f"<p>Migrations: {stats['status']['migrations']}</p>"
            f"<p>Scheduler: {stats['status']['scheduler']}</p>"
            f"<p>Telegram polling: {stats['status']['telegram']}</p>"
            f"<p>LLM: {stats['status']['llm']}</p>"
            f"<p>LLM last success: {stats['status']['llm_last_success']}</p>"
            "<h2>Settings</h2>"
            f"<p>TZ: {stats['settings']['tz']}</p>"
            f"<p>Weekly review: {stats['settings']['weekly_review_time']}</p>"
            f"<p>LLM enabled: {stats['settings']['llm_enabled']}</p>"
            f"<p>LLM provider: {stats['settings']['llm_provider']}</p>"
            f"<p>LLM model: {stats['settings']['llm_model']}</p>"
            "<h2>Recent errors</h2>"
            f"<p>{errors_html}</p>"
            "</body></html>"
        )

    @app.post("/admin/selftest")
    async def admin_selftest(
        user: str = Depends(auth_dependency),
        session: AsyncSession = Depends(get_session),
    ) -> JSONResponse:
        result = await run_selftest(session, settings, scheduler_running, llm_client)
        return JSONResponse(result)

    @app.get("/admin/stats.json")
    async def admin_stats(
        user: str = Depends(auth_dependency),
        session: AsyncSession = Depends(get_session),
    ) -> JSONResponse:
        stats = await build_stats(session, settings, scheduler_running, llm_client)
        return JSONResponse(stats)

    return app


async def _check_db(session: AsyncSession) -> None:
    await session.execute(text("SELECT 1"))


async def _check_migrations(session: AsyncSession) -> None:
    result = await session.execute(text("SELECT version_num FROM alembic_version"))
    current = result.scalar_one_or_none()
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    if current != head:
        raise RuntimeError(f"migrations not at head: {current} != {head}")


async def build_stats(
    session: AsyncSession,
    settings: Settings,
    scheduler_running: callable,
    llm_client: OllamaClient | None,
) -> dict:
    table_counts = {}
    for table in (
        "tasks",
        "inbox_items",
        "habits",
        "habit_logs",
        "mood_entries",
        "goals",
        "apple_health_raw_records",
        "apple_health_daily_aggregates",
        "pending_actions",
    ):
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            table_counts[table] = result.scalar_one()
        except Exception:
            table_counts[table] = "n/a"

    db_size = "n/a"
    try:
        result = await session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
        db_size = result.scalar_one()
    except Exception:
        db_size = "n/a"

    status = {
        "db": "ok",
        "migrations": "ok",
        "scheduler": "running" if scheduler_running() else "stopped",
        "telegram": "running" if BOT_STATUS.polling_started else "stopped",
        "llm": "enabled" if settings.llm_enabled else "disabled",
        "llm_last_success": LLM_STATUS.last_success_at.isoformat() if LLM_STATUS.last_success_at else None,
    }

    return {
        "db_size": db_size,
        "table_counts": table_counts,
        "status": status,
        "settings": {
            "tz": settings.tz,
            "weekly_review_time": settings.weekly_review_time,
            "llm_enabled": settings.llm_enabled,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.ollama_model,
        },
        "recent_errors": [LLM_STATUS.last_error] if LLM_STATUS.last_error else [],
    }


async def run_selftest(
    session: AsyncSession,
    settings: Settings,
    scheduler_running: callable,
    llm_client: OllamaClient | None,
) -> dict:
    results = {}
    try:
        await _check_db(session)
        results["db"] = "ok"
    except Exception as exc:
        results["db"] = f"fail: {exc}"

    try:
        await _check_migrations(session)
        results["migrations"] = "ok"
    except Exception as exc:
        results["migrations"] = f"fail: {exc}"

    results["scheduler"] = "ok" if scheduler_running() else "stopped"

    try:
        async with session.begin():
            await session.execute(text("SELECT 1"))
        results["transaction"] = "ok"
    except Exception as exc:
        results["transaction"] = f"fail: {exc}"

    try:
        if settings.llm_enabled and llm_client:
            text = await llm_client.generate("ping")
            results["llm"] = "ok" if text else "empty"
        else:
            results["llm"] = "skipped"
    except Exception as exc:
        results["llm"] = f"fail: {exc}"

    try:
        await asyncio.to_thread(_disk_check)
        results["disk"] = "ok"
    except Exception as exc:
        results["disk"] = f"fail: {exc}"

    return results


def _disk_check() -> None:
    path = "/tmp/admin_selftest.txt"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ok")
