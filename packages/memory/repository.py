from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class MemoryEntry:
    id: str
    user_id: str
    task_id: str | None
    content: str
    embedding: list[float]
    metadata: dict
    created_at: float


class MemoryStore(Protocol):
    def add_entry(
        self,
        user_id: str,
        content: str,
        embedding: list[float],
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        ...

    def search(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        task_id: str | None = None,
    ) -> list[dict]:
        ...

