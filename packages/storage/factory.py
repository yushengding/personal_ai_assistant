from __future__ import annotations

import os
from pathlib import Path

from packages.storage.postgres_store import PostgresStateStore
from packages.storage.repository import TaskStore
from packages.storage.state_store import StateStore


def _parse_simple_toml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or raw.startswith("["):
            continue
        if "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        values[k.strip()] = v.strip().strip('"')
    return values


def create_task_store() -> TaskStore:
    config_path = Path(os.getenv("PAI_DB_CONFIG", "configs/database.toml"))
    cfg = _parse_simple_toml(config_path)

    driver = os.getenv("PAI_DB_DRIVER", cfg.get("driver", "sqlite")).lower()

    if driver == "postgres":
        dsn = os.getenv("PAI_POSTGRES_DSN", cfg.get("postgres_dsn", "")).strip()
        if not dsn:
            raise RuntimeError("Postgres driver selected but no postgres_dsn configured")
        return PostgresStateStore(dsn)

    sqlite_path = os.getenv("PAI_SQLITE_PATH", cfg.get("sqlite_path", "data/state.db"))
    return StateStore(db_path=sqlite_path)

