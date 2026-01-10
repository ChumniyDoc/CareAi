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


@dataclass(slots=True)
class IntentResult:
    intent: str
    reply: str
    proposals: list[Proposal]
    valid_json: bool


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


def parse_intent_response(raw_text: str) -> IntentResult:
    if not raw_text:
        return IntentResult(intent="chat", reply="", proposals=[], valid_json=True)
    try:
        payload = orjson.loads(raw_text)
    except orjson.JSONDecodeError:
        return IntentResult(intent="chat", reply=raw_text.strip(), proposals=[], valid_json=False)
    if not isinstance(payload, dict):
        return IntentResult(intent="chat", reply=raw_text.strip(), proposals=[], valid_json=False)
    reply = str(payload.get("reply", "")).strip()
    intent = str(payload.get("intent", "chat")).strip() or "chat"
    proposals: list[Proposal] = []
    for item in payload.get("proposals", []) or []:
        tool = item.get("tool")
        args = item.get("args") or {}
        if tool:
            proposals.append(Proposal(tool=tool, args=args, reason=item.get("reason")))
    return IntentResult(intent=intent, reply=reply, proposals=proposals, valid_json=True)
