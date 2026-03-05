from __future__ import annotations

from typing import Dict, Protocol

from packages.agent_runtime.models import Task


class TaskStore(Protocol):
    def save_task(self, task: Task) -> None:
        ...

    def load_tasks(self) -> Dict[str, Task]:
        ...

    def query_tasks(self, page: int = 1, page_size: int = 20, status: str | None = None) -> dict:
        ...

    def query_history(self, page: int = 1, page_size: int = 50) -> dict:
        ...

