from __future__ import annotations

from typing import Any


def build_avatar_runtime_state(task_status: str, emotion_map: dict[str, str]) -> dict[str, Any]:
    emotion = emotion_map.get(task_status, emotion_map.get("idle", "neutral"))
    speaking = task_status == "running"
    return {
        "task_status": task_status,
        "emotion": emotion,
        "speaking": speaking,
    }

