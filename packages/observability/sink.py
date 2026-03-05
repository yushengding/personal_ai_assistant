from __future__ import annotations

from typing import Protocol


class MetricsSink(Protocol):
    def emit(self, event_type: str, payload: dict) -> None:
        ...

