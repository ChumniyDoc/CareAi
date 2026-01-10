from __future__ import annotations

from aiogram import Router

from bot.tg.handlers import (
    dashboard,
    export_delete,
    goals,
    habits,
    health_import,
    insights,
    mood,
    schedule,
    settings,
    start_help,
    tasks,
)

router = Router()
router.include_router(start_help.router)
router.include_router(tasks.router)
router.include_router(goals.router)
router.include_router(mood.router)
router.include_router(habits.router)
router.include_router(schedule.router)
router.include_router(health_import.router)
router.include_router(dashboard.router)
router.include_router(export_delete.router)
router.include_router(settings.router)
router.include_router(insights.router)
