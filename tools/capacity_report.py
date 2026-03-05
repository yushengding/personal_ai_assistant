from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB_PATH = Path("data/state.db")


def timed_query(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    t0 = time.perf_counter()
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    dt_ms = (time.perf_counter() - t0) * 1000
    return rows, round(dt_ms, 3)


def main() -> None:
    if not DB_PATH.exists():
        print(f"db not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    table_counts = {}
    for tbl in ["task_state", "tasks", "subtasks", "decision_tickets", "checkpoints", "task_metrics"]:
        try:
            c = conn.execute(f"SELECT COUNT(1) FROM {tbl}").fetchone()[0]
        except sqlite3.OperationalError:
            c = None
        table_counts[tbl] = c

    q1, t1 = timed_query(conn, "SELECT task_id, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 50")
    q2, t2 = timed_query(
        conn,
        """
        SELECT t.task_id, t.title, m.planned_seconds, m.actual_seconds, m.error_rate
        FROM task_metrics m JOIN tasks t ON t.task_id = m.task_id
        ORDER BY m.updated_at DESC LIMIT 50
        """,
    )

    size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 3)

    print("=== Capacity Report ===")
    print(f"db_path: {DB_PATH}")
    print(f"db_size_mb: {size_mb}")
    print("table_counts:")
    for k, v in table_counts.items():
        print(f"  - {k}: {v}")

    print("benchmark_queries:")
    print(f"  - tasks_latest_50: {t1} ms, rows={len(q1)}")
    print(f"  - history_latest_50: {t2} ms, rows={len(q2)}")


if __name__ == "__main__":
    main()
