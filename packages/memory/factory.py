from __future__ import annotations

from pathlib import Path

from packages.memory.pgvector_memory_store import PgVectorMemoryStore
from packages.memory.repository import MemoryStore
from packages.memory.sqlite_memory_store import SqliteMemoryStore
from packages.storage.factory import _parse_simple_toml


def create_memory_store() -> MemoryStore:
    cfg = _parse_simple_toml(Path("configs/database.toml"))

    db_driver = cfg.get("driver", "sqlite").lower()
    vector_provider = cfg.get("provider", "pgvector").lower()
    embedding_dim = int(cfg.get("embedding_dim", "1536"))

    if db_driver == "postgres" and vector_provider == "pgvector":
        dsn = cfg.get("postgres_dsn", "").strip()
        if not dsn:
            raise RuntimeError("pgvector selected but postgres_dsn is empty")
        return PgVectorMemoryStore(dsn=dsn, embedding_dim=embedding_dim)

    sqlite_path = cfg.get("sqlite_path", "data/state.db")
    return SqliteMemoryStore(db_path=sqlite_path)

