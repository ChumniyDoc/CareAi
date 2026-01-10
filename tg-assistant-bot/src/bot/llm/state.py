from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(slots=True)
class LlmStatus:
    last_success_at: dt.datetime | None = None
    last_error: str | None = None


LLM_STATUS = LlmStatus()
