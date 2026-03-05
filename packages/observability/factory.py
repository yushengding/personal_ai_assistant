from __future__ import annotations

from pathlib import Path

from packages.observability.clickhouse_sink import ClickHouseMetricsSink
from packages.observability.sink import MetricsSink
from packages.observability.sqlite_sink import SqliteMetricsSink
from packages.storage.factory import _parse_simple_toml


def create_metrics_sink() -> MetricsSink:
    cfg = _parse_simple_toml(Path("configs/database.toml"))
    backend = cfg.get("backend", "sqlite").lower()

    if backend == "clickhouse":
        dsn = cfg.get("clickhouse_dsn", "").strip()
        if not dsn:
            raise RuntimeError("metrics backend clickhouse selected but clickhouse_dsn is empty")
        return ClickHouseMetricsSink(dsn)

    sqlite_path = cfg.get("sqlite_path", "data/state.db")
    return SqliteMetricsSink(db_path=sqlite_path)

