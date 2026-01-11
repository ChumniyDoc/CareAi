from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(slots=True)
class BotStatus:
    polling_started: bool = False
    polling_started_at: dt.datetime | None = None
    last_update_at: dt.datetime | None = None


BOT_STATUS = BotStatus()
