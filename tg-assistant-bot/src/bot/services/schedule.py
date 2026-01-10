from __future__ import annotations

import calendar
import datetime as dt


def parse_pattern(pattern: str) -> tuple[int, int]:
    work, rest = pattern.split("/")
    return int(work), int(rest)


def is_workday(date: dt.date, start_date: dt.date, pattern: str) -> bool:
    work_days, rest_days = parse_pattern(pattern)
    cycle = work_days + rest_days
    delta = (date - start_date).days
    position = delta % cycle
    return position < work_days


def month_calendar(year: int, month: int) -> list[list[int]]:
    return calendar.monthcalendar(year, month)
