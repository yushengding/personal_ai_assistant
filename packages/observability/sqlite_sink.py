from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path

from packages.observability.sink import MetricsSink


class SqliteMetricsSink(MetricsSink):
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
                CREATE TABLE IF NOT EXISTS metrics_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_events_type_time ON metrics_events(event_type, created_at)")
            conn.commit()

    def emit(self, event_type: str, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO metrics_events(event_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    event_type,
                    json.dumps(payload, ensure_ascii=False),
                    time.time(),
                ),
            )
            conn.commit()

