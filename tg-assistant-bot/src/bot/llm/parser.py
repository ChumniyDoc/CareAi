from __future__ import annotations

from dataclasses import dataclass

import orjson


@dataclass(slots=True)
class Proposal:
    tool: str
    args: dict
    reason: str | None = None


@dataclass(slots=True)
class LlmResult:
    response: str
    proposals: list[Proposal]


def parse_llm_response(raw_text: str) -> LlmResult:
    if not raw_text:
        return LlmResult(response="", proposals=[])
    try:
        payload = orjson.loads(raw_text)
    except orjson.JSONDecodeError:
        return LlmResult(response=raw_text.strip(), proposals=[])
    if not isinstance(payload, dict):
        return LlmResult(response=raw_text.strip(), proposals=[])
    response = str(payload.get("response", "")).strip()
    proposals: list[Proposal] = []
    for item in payload.get("proposals", []) or []:
        tool = item.get("tool")
        args = item.get("args") or {}
        if tool:
            proposals.append(Proposal(tool=tool, args=args, reason=item.get("reason")))
    return LlmResult(response=response, proposals=proposals)
