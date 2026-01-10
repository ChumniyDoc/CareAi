from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(slots=True)
class AlcoholLogResult:
    relapse: bool
    portion_count: int


def normalize_trigger(text: str) -> bool:
    return "тяга" in text.lower()


def handle_alcohol_portion(count: int) -> AlcoholLogResult:
    relapse = count > 0
    return AlcoholLogResult(relapse=relapse, portion_count=count)


def today(timezone: str) -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()
