from __future__ import annotations

from typing import Dict

from packages.agent_runtime.models import Task


class DashboardMetrics:
    def build_overview(self, tasks: Dict[str, Task]) -> dict:
        all_tasks = list(tasks.values())
        active = [t for t in all_tasks if t.status in {"queued", "planning", "running", "waiting_decision"}]
        completed = [t for t in all_tasks if t.status == "completed" and t.completed_at and t.started_at]
        failed = [t for t in all_tasks if t.status == "failed"]

        eta_errors = []
        for task in completed:
            actual = float(task.completed_at - task.started_at)
            if task.planned_seconds > 0:
                eta_errors.append(abs(actual - task.planned_seconds) / task.planned_seconds)

        mape = sum(eta_errors) / len(eta_errors) if eta_errors else 0.0

        return {
            "active_tasks": len(active),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "avg_progress_active": round(sum(t.progress for t in active) / len(active), 4) if active else 0.0,
            "mape": round(mape, 4),
        }

    def build_history(self, tasks: Dict[str, Task]) -> list[dict]:
        history = []
        for task in tasks.values():
            if not task.started_at or not task.completed_at:
                continue
            actual = float(task.completed_at - task.started_at)
            history.append(
                {
                    "task_id": task.id,
                    "title": task.title,
                    "planned_seconds": task.planned_seconds,
                    "actual_seconds": round(actual, 2),
                    "absolute_error": round(abs(actual - task.planned_seconds), 2),
                    "error_rate": round(abs(actual - task.planned_seconds) / task.planned_seconds, 4)
                    if task.planned_seconds > 0
                    else 0.0,
                    "status": task.status,
                }
            )
        history.sort(key=lambda x: x["task_id"])
        return history

