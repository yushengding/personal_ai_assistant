from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict

from packages.agent_runtime.models import Task, task_from_dict, task_to_dict


class StateStore:
    def __init__(self, db_path: str = "data/state.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_state (
                    task_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def save_task(self, task: Task) -> None:
        payload = json.dumps(task_to_dict(task), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_state(task_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(task_id) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (task.id, payload),
            )
            conn.commit()

    def load_tasks(self) -> Dict[str, Task]:
        tasks: Dict[str, Task] = {}
        with self._connect() as conn:
            rows = conn.execute("SELECT task_id, payload FROM task_state").fetchall()
        for row in rows:
            data = json.loads(row["payload"])
            task = task_from_dict(data)
            tasks[row["task_id"]] = task
        return tasks

