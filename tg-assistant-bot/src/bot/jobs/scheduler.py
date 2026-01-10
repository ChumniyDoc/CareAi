from __future__ import annotations

import asyncio
import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import tz


class SchedulerService:
    def __init__(self, timezone: str) -> None:
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=tz.gettz(timezone))

    def start(self) -> None:
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown()

    def schedule_once(self, run_at: dt.datetime, coro, *args) -> None:
        self.scheduler.add_job(lambda: asyncio.create_task(coro(*args)), "date", run_date=run_at)
