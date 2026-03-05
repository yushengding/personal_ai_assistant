from __future__ import annotations

import json
import math
import sqlite3
import time
import uuid
from pathlib import Path

from packages.memory.repository import MemoryStore


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return -1.0
    return dot / (na * nb)


class SqliteMemoryStore(MemoryStore):
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
                CREATE TABLE IF NOT EXISTS memory_vectors (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_id TEXT,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_user_task ON memory_vectors(user_id, task_id)")
            conn.commit()

    def add_entry(
        self,
        user_id: str,
        content: str,
        embedding: list[float],
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        row_id = str(uuid.uuid4())
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_vectors(id, user_id, task_id, content, embedding_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    user_id,
                    task_id,
                    content,
                    json.dumps(embedding, ensure_ascii=False),
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now,
                ),
            )
            conn.commit()
        return row_id

    def search(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        task_id: str | None = None,
    ) -> list[dict]:
        where = "WHERE user_id = ?"
        params: list = [user_id]
        if task_id:
            where += " AND task_id = ?"
            params.append(task_id)

        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT id, user_id, task_id, content, embedding_json, metadata_json, created_at FROM memory_vectors {where}",
                params,
            ).fetchall()

        scored = []
        for row in rows:
            emb = json.loads(row["embedding_json"])
            score = _cosine(query_embedding, emb)
            scored.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "task_id": row["task_id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata_json"]),
                    "score": round(float(score), 6),
                    "created_at": row["created_at"],
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: max(1, min(50, top_k))]

