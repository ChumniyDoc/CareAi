from __future__ import annotations

import datetime as dt

import dateparser
from dateutil import tz


def parse_task_text(text: str, timezone: str) -> tuple[str, dt.datetime | None]:
    settings = {
        "TIMEZONE": timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
        "LANGUAGE": "ru",
    }
    parsed = dateparser.parse(text, settings=settings)
    if parsed:
        title = text
        return title, parsed
    return text, None


def local_date(timezone: str) -> dt.date:
    return dt.datetime.now(tz.gettz(timezone)).date()
