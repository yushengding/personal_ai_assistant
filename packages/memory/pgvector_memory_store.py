from __future__ import annotations

import json
import uuid

from packages.memory.repository import MemoryStore

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None


class PgVectorMemoryStore(MemoryStore):
    def __init__(self, dsn: str, embedding_dim: int = 1536) -> None:
        self.dsn = dsn
        self.embedding_dim = embedding_dim

    def _ensure_driver(self) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is not installed. Install psycopg[binary] for pgvector backend.")

    def _connect(self):
        self._ensure_driver()
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _vec_literal(self, embedding: list[float]) -> str:
        if len(embedding) != self.embedding_dim:
            raise ValueError(f"embedding dim mismatch, expected {self.embedding_dim}, got {len(embedding)}")
        return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

    def add_entry(
        self,
        user_id: str,
        content: str,
        embedding: list[float],
        task_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        vec = self._vec_literal(embedding)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memory_vectors(id, user_id, task_id, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                    """,
                    (entry_id, user_id, task_id, content, vec, json.dumps(metadata or {}, ensure_ascii=False)),
                )
            conn.commit()
        return entry_id

    def search(
        self,
        user_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        task_id: str | None = None,
    ) -> list[dict]:
        vec = self._vec_literal(query_embedding)
        where = "WHERE user_id = %s"
        params: list = [user_id]
        if task_id:
            where += " AND task_id = %s"
            params.append(task_id)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, user_id, task_id, content, metadata, created_at,
                           (1 - (embedding <=> %s::vector)) AS score
                    FROM memory_vectors
                    {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    [vec, *params, vec, max(1, min(50, top_k))],
                )
                rows = cur.fetchall()

        for r in rows:
            r["score"] = round(float(r["score"]), 6)
        return rows

