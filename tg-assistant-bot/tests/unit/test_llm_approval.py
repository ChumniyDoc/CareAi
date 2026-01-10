import pytest

from bot.db import models
from bot.llm.approval import execute_if_approved


@pytest.mark.asyncio
async def test_execute_if_approved_skips_when_pending():
    action = models.PendingAction(
        user_id=1,
        tool_name="create_task",
        tool_args_json={},
        status="pending",
    )

    async def _executor(_action):
        raise AssertionError("executor should not run")

    executed, result = await execute_if_approved(action, _executor)
    assert executed is False
    assert result is None


@pytest.mark.asyncio
async def test_execute_if_approved_runs_when_approved():
    action = models.PendingAction(
        user_id=1,
        tool_name="create_task",
        tool_args_json={},
        status="approved",
    )

    async def _executor(_action):
        return "ok"

    executed, result = await execute_if_approved(action, _executor)
    assert executed is True
    assert result == "ok"
    assert action.status == "executed"
