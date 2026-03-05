from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from packages.agent_runtime.models import Checkpoint, DecisionTicket, ImportanceLevel, SubTask, Task, task_from_dict, task_to_dict


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
            # Backward-compatible blob snapshot table.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_state (
                    task_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    core_pause_level INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    eta_seconds REAL,
                    eta_confidence REAL NOT NULL,
                    planned_seconds INTEGER NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    error TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subtasks (
                    task_id TEXT NOT NULL,
                    subtask_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    estimate_seconds INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    dependencies_json TEXT NOT NULL,
                    requires_decision INTEGER NOT NULL,
                    assigned_agent_id TEXT,
                    status TEXT NOT NULL,
                    started_at REAL,
                    finished_at REAL,
                    actual_seconds REAL,
                    PRIMARY KEY (task_id, subtask_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    subtask_id TEXT NOT NULL,
                    importance_level INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    requires_pause INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    resolved_at REAL,
                    resolution TEXT,
                    checkpoint_ref TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    reason TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_metrics (
                    task_id TEXT PRIMARY KEY,
                    planned_seconds INTEGER NOT NULL,
                    actual_seconds REAL,
                    absolute_error REAL,
                    error_rate REAL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status_level ON decision_tickets(status, importance_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_task_status ON subtasks(task_id, status)")
            self._ensure_column(conn, "subtasks", "assigned_agent_id", "TEXT")
            conn.commit()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        cols = {r["name"] for r in rows}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def save_task(self, task: Task) -> None:
        payload = json.dumps(task_to_dict(task), ensure_ascii=False)

        with self._connect() as conn:
            # Keep snapshot for compatibility/recovery.
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

            # Upsert task row.
            conn.execute(
                """
                INSERT INTO tasks(
                    task_id, title, goal, created_at, core_pause_level, status, progress,
                    eta_seconds, eta_confidence, planned_seconds, started_at, completed_at, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    title=excluded.title,
                    goal=excluded.goal,
                    created_at=excluded.created_at,
                    core_pause_level=excluded.core_pause_level,
                    status=excluded.status,
                    progress=excluded.progress,
                    eta_seconds=excluded.eta_seconds,
                    eta_confidence=excluded.eta_confidence,
                    planned_seconds=excluded.planned_seconds,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    error=excluded.error
                """,
                (
                    task.id,
                    task.title,
                    task.goal,
                    task.created_at,
                    int(task.core_pause_level),
                    task.status,
                    float(task.progress),
                    task.eta_seconds,
                    float(task.eta_confidence),
                    int(task.planned_seconds),
                    task.started_at,
                    task.completed_at,
                    task.error,
                ),
            )

            # Rebuild detail rows for this task.
            conn.execute("DELETE FROM subtasks WHERE task_id = ?", (task.id,))
            for st in task.subtasks.values():
                conn.execute(
                    """
                    INSERT INTO subtasks(
                        task_id, subtask_id, name, estimate_seconds, weight,
                        dependencies_json, requires_decision, assigned_agent_id, status, started_at, finished_at, actual_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.id,
                        st.id,
                        st.name,
                        int(st.estimate_seconds),
                        float(st.weight),
                        json.dumps(st.dependencies, ensure_ascii=False),
                        1 if st.requires_decision else 0,
                        st.assigned_agent_id,
                        st.status,
                        st.started_at,
                        st.finished_at,
                        st.actual_seconds,
                    ),
                )

            conn.execute("DELETE FROM decision_tickets WHERE task_id = ?", (task.id,))
            for tk in task.decision_tickets.values():
                conn.execute(
                    """
                    INSERT INTO decision_tickets(
                        ticket_id, task_id, subtask_id, importance_level, summary, impact,
                        recommended_action, requires_pause, status, created_at, resolved_at,
                        resolution, checkpoint_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tk.id,
                        tk.task_id,
                        tk.subtask_id,
                        int(tk.importance_level),
                        tk.summary,
                        tk.impact,
                        tk.recommended_action,
                        1 if tk.requires_pause else 0,
                        tk.status,
                        tk.created_at,
                        tk.resolved_at,
                        tk.resolution,
                        tk.checkpoint_ref,
                    ),
                )

            conn.execute("DELETE FROM checkpoints WHERE task_id = ?", (task.id,))
            for cp in task.checkpoints:
                conn.execute(
                    """
                    INSERT INTO checkpoints(checkpoint_id, task_id, created_at, reason, snapshot_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        cp.id,
                        cp.task_id,
                        cp.created_at,
                        cp.reason,
                        json.dumps(cp.snapshot, ensure_ascii=False),
                    ),
                )

            actual_seconds: Optional[float] = None
            abs_error: Optional[float] = None
            error_rate: Optional[float] = None
            if task.started_at is not None and task.completed_at is not None:
                actual_seconds = float(task.completed_at - task.started_at)
                abs_error = abs(actual_seconds - task.planned_seconds)
                if task.planned_seconds > 0:
                    error_rate = abs_error / task.planned_seconds

            conn.execute(
                """
                INSERT INTO task_metrics(task_id, planned_seconds, actual_seconds, absolute_error, error_rate, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(task_id) DO UPDATE SET
                    planned_seconds=excluded.planned_seconds,
                    actual_seconds=excluded.actual_seconds,
                    absolute_error=excluded.absolute_error,
                    error_rate=excluded.error_rate,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (task.id, task.planned_seconds, actual_seconds, abs_error, error_rate),
            )

            conn.commit()

    def load_tasks(self) -> Dict[str, Task]:
        with self._connect() as conn:
            has_structured = conn.execute("SELECT COUNT(1) AS c FROM tasks").fetchone()["c"] > 0

            if not has_structured:
                return self._load_tasks_from_blob(conn)

            task_rows = conn.execute("SELECT * FROM tasks").fetchall()
            subtasks_by_task = self._fetch_subtasks_grouped(conn)
            tickets_by_task = self._fetch_tickets_grouped(conn)
            checkpoints_by_task = self._fetch_checkpoints_grouped(conn)

        tasks: Dict[str, Task] = {}
        for row in task_rows:
            task_id = row["task_id"]
            task = Task(
                id=task_id,
                title=row["title"],
                goal=row["goal"],
                created_at=row["created_at"],
                core_pause_level=ImportanceLevel(row["core_pause_level"]),
                status=row["status"],
                progress=row["progress"],
                eta_seconds=row["eta_seconds"],
                eta_confidence=row["eta_confidence"],
                planned_seconds=row["planned_seconds"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                subtasks=subtasks_by_task.get(task_id, {}),
                decision_tickets=tickets_by_task.get(task_id, {}),
                checkpoints=checkpoints_by_task.get(task_id, []),
                error=row["error"],
            )
            tasks[task_id] = task
        return tasks

    def _load_tasks_from_blob(self, conn: sqlite3.Connection) -> Dict[str, Task]:
        rows = conn.execute("SELECT task_id, payload FROM task_state").fetchall()
        tasks: Dict[str, Task] = {}
        for row in rows:
            data = json.loads(row["payload"])
            task = task_from_dict(data)
            tasks[row["task_id"]] = task
        return tasks

    def _fetch_subtasks_grouped(self, conn: sqlite3.Connection) -> Dict[str, Dict[str, SubTask]]:
        rows = conn.execute("SELECT * FROM subtasks").fetchall()
        grouped: Dict[str, Dict[str, SubTask]] = {}
        for row in rows:
            task_id = row["task_id"]
            grouped.setdefault(task_id, {})[row["subtask_id"]] = SubTask(
                id=row["subtask_id"],
                name=row["name"],
                estimate_seconds=row["estimate_seconds"],
                weight=row["weight"],
                dependencies=json.loads(row["dependencies_json"]),
                requires_decision=bool(row["requires_decision"]),
                assigned_agent_id=row["assigned_agent_id"],
                status=row["status"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
                actual_seconds=row["actual_seconds"],
            )
        return grouped

    def _fetch_tickets_grouped(self, conn: sqlite3.Connection) -> Dict[str, Dict[str, DecisionTicket]]:
        rows = conn.execute("SELECT * FROM decision_tickets").fetchall()
        grouped: Dict[str, Dict[str, DecisionTicket]] = {}
        for row in rows:
            task_id = row["task_id"]
            grouped.setdefault(task_id, {})[row["ticket_id"]] = DecisionTicket(
                id=row["ticket_id"],
                task_id=row["task_id"],
                subtask_id=row["subtask_id"],
                importance_level=ImportanceLevel(row["importance_level"]),
                summary=row["summary"],
                impact=row["impact"],
                recommended_action=row["recommended_action"],
                requires_pause=bool(row["requires_pause"]),
                status=row["status"],
                created_at=row["created_at"],
                resolved_at=row["resolved_at"],
                resolution=row["resolution"],
                checkpoint_ref=row["checkpoint_ref"],
            )
        return grouped

    def _fetch_checkpoints_grouped(self, conn: sqlite3.Connection) -> Dict[str, list[Checkpoint]]:
        rows = conn.execute("SELECT * FROM checkpoints ORDER BY created_at ASC").fetchall()
        grouped: Dict[str, list[Checkpoint]] = {}
        for row in rows:
            task_id = row["task_id"]
            grouped.setdefault(task_id, []).append(
                Checkpoint(
                    id=row["checkpoint_id"],
                    task_id=task_id,
                    created_at=row["created_at"],
                    reason=row["reason"],
                    snapshot=json.loads(row["snapshot_json"]),
                )
            )
        return grouped

    def query_tasks(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> dict:
        page = max(1, page)
        page_size = min(200, max(1, page_size))
        offset = (page - 1) * page_size

        where_sql = ""
        params: list = []
        if status:
            where_sql = "WHERE status = ?"
            params.append(status)

        with self._connect() as conn:
            total = conn.execute(f"SELECT COUNT(1) AS c FROM tasks {where_sql}", params).fetchone()["c"]
            rows = conn.execute(
                f"""
                SELECT task_id, title, goal, status, progress, eta_seconds, eta_confidence,
                       planned_seconds, created_at, started_at, completed_at
                FROM tasks
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()

        return {
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": [dict(r) for r in rows],
        }

    def query_history(self, page: int = 1, page_size: int = 50) -> dict:
        page = max(1, page)
        page_size = min(500, max(1, page_size))
        offset = (page - 1) * page_size

        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(1) AS c FROM task_metrics").fetchone()["c"]
            rows = conn.execute(
                """
                SELECT t.task_id, t.title, t.status,
                       m.planned_seconds, m.actual_seconds, m.absolute_error, m.error_rate, m.updated_at
                FROM task_metrics m
                JOIN tasks t ON t.task_id = m.task_id
                ORDER BY m.updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset),
            ).fetchall()

        return {
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": [dict(r) for r in rows],
        }

