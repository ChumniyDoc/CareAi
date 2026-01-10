from __future__ import annotations

from collections.abc import Awaitable, Callable

from bot.db import models


async def execute_if_approved(
    action: models.PendingAction,
    executor: Callable[[models.PendingAction], Awaitable[str]],
) -> tuple[bool, str | None]:
    if action.status != "approved":
        return False, None
    result = await executor(action)
    action.status = "executed"
    return True, result
