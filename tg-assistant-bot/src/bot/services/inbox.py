from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ClassificationResult:
    kind: str
    confidence: float


def classify_message(text: str) -> ClassificationResult:
    lowered = text.lower()
    if any(token in lowered for token in ("задача", "купить", "сделать", "встреча")):
        return ClassificationResult(kind="task", confidence=0.6)
    if any(token in lowered for token in ("настроение", "муд", "mood")):
        return ClassificationResult(kind="mood", confidence=0.5)
    if any(token in lowered for token in ("привычка", "habit")):
        return ClassificationResult(kind="habit", confidence=0.5)
    return ClassificationResult(kind="note", confidence=0.4)
