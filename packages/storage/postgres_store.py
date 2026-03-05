from __future__ import annotations

import json
from typing import Dict, Optional

from packages.agent_runtime.models import Checkpoint, DecisionTicket, ImportanceLevel, SubTask, Task
from packages.storage.repository import TaskStore

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover - optional dependency in scaffold stage
    psycopg = None
    dict_row = None


class PostgresStateStore(TaskStore):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _ensure_driver(self) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is not installed. Install psycopg[binary] to use PostgreSQL store.")

    def _connect(self):
        self._ensure_driver()
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def save_task(self, task: Task) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks(
                        task_id, title, goal, created_at, core_pause_level, status, progress,
                        eta_seconds, eta_confidence, planned_seconds, started_at, completed_at, error
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(task_id) DO UPDATE SET
                        title=EXCLUDED.title,
                        goal=EXCLUDED.goal,
                        created_at=EXCLUDED.created_at,
                        core_pause_level=EXCLUDED.core_pause_level,
                        status=EXCLUDED.status,
                        progress=EXCLUDED.progress,
                        eta_seconds=EXCLUDED.eta_seconds,
                        eta_confidence=EXCLUDED.eta_confidence,
                        planned_seconds=EXCLUDED.planned_seconds,
                        started_at=EXCLUDED.started_at,
                        completed_at=EXCLUDED.completed_at,
                        error=EXCLUDED.error
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

                cur.execute("DELETE FROM subtasks WHERE task_id = %s", (task.id,))
                for st in task.subtasks.values():
                    cur.execute(
                        """
                        INSERT INTO subtasks(
                            task_id, subtask_id, name, estimate_seconds, weight,
                            dependencies_json, requires_decision, assigned_agent_id, status, started_at, finished_at, actual_seconds
                        ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            task.id,
                            st.id,
                            st.name,
                            int(st.estimate_seconds),
                            float(st.weight),
                            json.dumps(st.dependencies, ensure_ascii=False),
                            bool(st.requires_decision),
                            st.assigned_agent_id,
                            st.status,
                            st.started_at,
                            st.finished_at,
                            st.actual_seconds,
                        ),
                    )

                cur.execute("DELETE FROM decision_tickets WHERE task_id = %s", (task.id,))
                for tk in task.decision_tickets.values():
                    cur.execute(
                        """
                        INSERT INTO decision_tickets(
                            ticket_id, task_id, subtask_id, importance_level, summary, impact,
                            recommended_action, requires_pause, status, created_at, resolved_at,
                            resolution, checkpoint_ref
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            tk.id,
                            tk.task_id,
                            tk.subtask_id,
                            int(tk.importance_level),
                            tk.summary,
                            tk.impact,
                            tk.recommended_action,
                            bool(tk.requires_pause),
                            tk.status,
                            tk.created_at,
                            tk.resolved_at,
                            tk.resolution,
                            tk.checkpoint_ref,
                        ),
                    )

                cur.execute("DELETE FROM checkpoints WHERE task_id = %s", (task.id,))
                for cp in task.checkpoints:
                    cur.execute(
                        """
                        INSERT INTO checkpoints(checkpoint_id, task_id, created_at, reason, snapshot_json)
                        VALUES (%s, %s, %s, %s, %s::jsonb)
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

                cur.execute(
                    """
                    INSERT INTO task_metrics(task_id, planned_seconds, actual_seconds, absolute_error, error_rate, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(task_id) DO UPDATE SET
                        planned_seconds=EXCLUDED.planned_seconds,
                        actual_seconds=EXCLUDED.actual_seconds,
                        absolute_error=EXCLUDED.absolute_error,
                        error_rate=EXCLUDED.error_rate,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (task.id, task.planned_seconds, actual_seconds, abs_error, error_rate),
                )
            conn.commit()

    def load_tasks(self) -> Dict[str, Task]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks")
                task_rows = cur.fetchall()
                if not task_rows:
                    return {}

                cur.execute("SELECT * FROM subtasks")
                subtasks_by_task = self._group_subtasks(cur.fetchall())

                cur.execute("SELECT * FROM decision_tickets")
                tickets_by_task = self._group_tickets(cur.fetchall())

                cur.execute("SELECT * FROM checkpoints ORDER BY created_at ASC")
                checkpoints_by_task = self._group_checkpoints(cur.fetchall())

        tasks: Dict[str, Task] = {}
        for row in task_rows:
            task_id = row["task_id"]
            tasks[task_id] = Task(
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
        return tasks

    def query_tasks(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> dict:
        page = max(1, page)
        page_size = min(200, max(1, page_size))
        offset = (page - 1) * page_size

        where_sql = ""
        params: list = []
        if status:
            where_sql = "WHERE status = %s"
            params.append(status)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(1) AS c FROM tasks {where_sql}", params)
                total = cur.fetchone()["c"]
                cur.execute(
                    f"""
                    SELECT task_id, title, goal, status, progress, eta_seconds, eta_confidence,
                           planned_seconds, created_at, started_at, completed_at
                    FROM tasks
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, page_size, offset],
                )
                rows = cur.fetchall()

        return {
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": rows,
        }

    def query_history(self, page: int = 1, page_size: int = 50) -> dict:
        page = max(1, page)
        page_size = min(500, max(1, page_size))
        offset = (page - 1) * page_size

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(1) AS c FROM task_metrics")
                total = cur.fetchone()["c"]
                cur.execute(
                    """
                    SELECT t.task_id, t.title, t.status,
                           m.planned_seconds, m.actual_seconds, m.absolute_error, m.error_rate, m.updated_at
                    FROM task_metrics m
                    JOIN tasks t ON t.task_id = m.task_id
                    ORDER BY m.updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (page_size, offset),
                )
                rows = cur.fetchall()

        return {
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": rows,
        }

    def _group_subtasks(self, rows: list[dict]) -> Dict[str, Dict[str, SubTask]]:
        grouped: Dict[str, Dict[str, SubTask]] = {}
        for row in rows:
            task_id = row["task_id"]
            deps = row["dependencies_json"]
            if isinstance(deps, str):
                deps = json.loads(deps)
            grouped.setdefault(task_id, {})[row["subtask_id"]] = SubTask(
                id=row["subtask_id"],
                name=row["name"],
                estimate_seconds=row["estimate_seconds"],
                weight=row["weight"],
                dependencies=list(deps),
                requires_decision=bool(row["requires_decision"]),
                assigned_agent_id=row.get("assigned_agent_id"),
                status=row["status"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
                actual_seconds=row["actual_seconds"],
            )
        return grouped

    def _group_tickets(self, rows: list[dict]) -> Dict[str, Dict[str, DecisionTicket]]:
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

    def _group_checkpoints(self, rows: list[dict]) -> Dict[str, list[Checkpoint]]:
        grouped: Dict[str, list[Checkpoint]] = {}
        for row in rows:
            task_id = row["task_id"]
            snapshot = row["snapshot_json"]
            if isinstance(snapshot, str):
                snapshot = json.loads(snapshot)
            grouped.setdefault(task_id, []).append(
                Checkpoint(
                    id=row["checkpoint_id"],
                    task_id=task_id,
                    created_at=row["created_at"],
                    reason=row["reason"],
                    snapshot=dict(snapshot),
                )
            )
        return grouped

