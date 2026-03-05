from __future__ import annotations

import json

from packages.observability.sink import MetricsSink

try:
    import clickhouse_connect
except Exception:  # pragma: no cover
    clickhouse_connect = None


class ClickHouseMetricsSink(MetricsSink):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.client = None

    def _ensure_client(self):
        if clickhouse_connect is None:
            raise RuntimeError("clickhouse-connect is not installed. Install requirements-clickhouse.txt")
        if self.client is None:
            # dsn format example: clickhouse://user:password@host:8123/database
            # parse lightweight
            no_proto = self.dsn.replace("clickhouse://", "")
            creds_host, database = no_proto.split("/", 1)
            creds, host_port = creds_host.split("@", 1)
            user, password = creds.split(":", 1)
            host, port = host_port.split(":", 1)
            self.client = clickhouse_connect.get_client(
                host=host,
                port=int(port),
                username=user,
                password=password,
                database=database,
            )

    def emit(self, event_type: str, payload: dict) -> None:
        self._ensure_client()
        self.client.insert(
            "metrics_events",
            [[event_type, json.dumps(payload, ensure_ascii=False)]],
            column_names=["event_type", "payload_json"],
        )

