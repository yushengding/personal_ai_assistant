from __future__ import annotations

import asyncio
import random
import time
import uuid
from typing import Dict, Optional

from packages.agent_runtime.agent_manager import AgentManager
from packages.agent_runtime.models import Checkpoint, DecisionTicket, ImportanceLevel, SubTask, Task
from packages.agent_runtime.planner import plan_task
from packages.security_policy.decision import should_pause_for_decision
from packages.storage.repository import TaskStore


class TaskEngine:
    def __init__(
        self,
        max_parallel_subtasks: int = 3,
        store: Optional[TaskStore] = None,
        agent_manager: Optional[AgentManager] = None,
    ) -> None:
        self.max_parallel_subtasks = max_parallel_subtasks
        self.store = store
        self.agent_manager = agent_manager
        self.tasks: Dict[str, Task] = {}
        self._task_loops: Dict[str, asyncio.Task] = {}
        self._pause_events: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()
        self._load_from_store()

    def _load_from_store(self) -> None:
        if not self.store:
            return
        self.tasks = self.store.load_tasks()
        for task in self.tasks.values():
            self._pause_events[task.id] = asyncio.Event()
            self._pause_events[task.id].set()
            # Recover in-flight state after process restart.
            if task.status in {"running", "waiting_decision", "planning"}:
                task.status = "queued"
            for subtask in task.subtasks.values():
                if subtask.status == "running":
                    subtask.status = "ready"
                    subtask.started_at = None

    def _persist_task(self, task: Task) -> None:
        if self.store:
            self.store.save_task(task)

    async def create_task(self, title: str, goal: str, core_pause_level: str = "L0") -> Task:
        async with self._lock:
            task_id = str(uuid.uuid4())
            now = time.time()
            task = Task(
                id=task_id,
                title=title,
                goal=goal,
                created_at=now,
                core_pause_level=ImportanceLevel.from_str(core_pause_level),
            )
            plan_task(task)
            task.status = "queued"
            self.tasks[task_id] = task
            evt = asyncio.Event()
            evt.set()
            self._pause_events[task_id] = evt
            self._persist_task(task)
            return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def list_tasks(self) -> Dict[str, Task]:
        return self.tasks

    def assign_subtask(self, task_id: str, subtask_id: str, agent_id: str) -> dict:
        task = self._require_task(task_id)
        if subtask_id not in task.subtasks:
            raise ValueError("subtask not found")
        task.subtasks[subtask_id].assigned_agent_id = agent_id
        self._persist_task(task)
        return {"task_id": task_id, "subtask_id": subtask_id, "agent_id": agent_id}

    def task_dag(self, task_id: str) -> dict:
        task = self._require_task(task_id)
        nodes = []
        edges = []
        for st in task.subtasks.values():
            nodes.append(
                {
                    "id": st.id,
                    "name": st.name,
                    "status": st.status,
                    "estimate_seconds": st.estimate_seconds,
                    "assigned_agent_id": st.assigned_agent_id,
                }
            )
            for dep in st.dependencies:
                edges.append({"from": dep, "to": st.id})

        critical_path_seconds = self._estimate_critical_path(task)
        return {"task_id": task_id, "nodes": nodes, "edges": edges, "critical_path_seconds": critical_path_seconds}

    async def run_task(self, task_id: str) -> Task:
        task = self._require_task(task_id)
        if task.status in {"running", "completed"}:
            return task

        if task_id in self._task_loops and not self._task_loops[task_id].done():
            return task

        task.status = "running"
        if task.started_at is None:
            task.started_at = time.time()

        self._persist_task(task)
        loop_task = asyncio.create_task(self._run_loop(task_id))
        self._task_loops[task_id] = loop_task
        return task

    async def _run_loop(self, task_id: str) -> None:
        task = self._require_task(task_id)
        pause_evt = self._pause_events[task_id]
        running_workers: Dict[str, asyncio.Task] = {}

        try:
            while True:
                await pause_evt.wait()

                if task.status == "waiting_decision":
                    await asyncio.sleep(0.05)
                    continue

                for sid, worker in list(running_workers.items()):
                    if worker.done():
                        running_workers.pop(sid, None)
                        exc = worker.exception()
                        if exc:
                            task.status = "failed"
                            task.error = str(exc)
                            self._persist_task(task)
                            return

                if all(st.status in {"completed", "skipped"} for st in task.subtasks.values()):
                    task.recalculate_progress()
                    task.status = "completed"
                    task.completed_at = time.time()
                    task.eta_seconds = 0.0
                    task.eta_confidence = 0.95
                    self._persist_task(task)
                    return

                ready = task.runnable_subtasks()
                available_slots = self.max_parallel_subtasks - len(running_workers)

                selected: list[tuple[SubTask, Optional[str]]] = []
                for subtask in ready:
                    if len(selected) >= max(0, available_slots):
                        break

                    agent_id = None
                    if self.agent_manager and self.agent_manager.has_agents():
                        agent_id = self.agent_manager.reserve_for_subtask(
                            task.id, subtask.id, preferred_agent_id=subtask.assigned_agent_id
                        )
                        if not agent_id:
                            continue
                        subtask.assigned_agent_id = agent_id
                    selected.append((subtask, agent_id))

                for subtask, agent_id in selected:
                    worker = asyncio.create_task(self._execute_subtask(task, subtask, agent_id))
                    running_workers[subtask.id] = worker

                task.recalculate_progress()
                self._refresh_eta(task)

                if not running_workers and not ready and task.status != "waiting_decision":
                    task.status = "failed"
                    task.error = "Deadlock detected in subtask dependencies"
                    self._persist_task(task)
                    return

                self._persist_task(task)
                await asyncio.sleep(0.05)
        finally:
            for worker in running_workers.values():
                if not worker.done():
                    worker.cancel()

    async def _execute_subtask(self, task: Task, subtask: SubTask, agent_id: Optional[str] = None) -> None:
        subtask.status = "running"
        subtask.started_at = time.time()
        self._persist_task(task)

        duration = max(0.5, subtask.estimate_seconds * random.uniform(0.35, 0.75))
        await asyncio.sleep(duration)

        if subtask.requires_decision:
            checkpoint = self._create_checkpoint(task, reason=f"before_decision:{subtask.id}")
            level = random.choice([ImportanceLevel.L0_CORE, ImportanceLevel.L1_HIGH, ImportanceLevel.L2_NORMAL])
            ticket = DecisionTicket(
                id=str(uuid.uuid4()),
                task_id=task.id,
                subtask_id=subtask.id,
                importance_level=level,
                summary=f"子任务 {subtask.name} 需要决策",
                impact="继续执行可能影响最终质量与成本",
                recommended_action="approve",
                requires_pause=should_pause_for_decision(level, task.core_pause_level),
                created_at=time.time(),
                checkpoint_ref=checkpoint.id,
            )
            task.decision_tickets[ticket.id] = ticket

            if ticket.requires_pause:
                subtask.status = "blocked"
                task.status = "waiting_decision"
                self._pause_events[task.id].clear()
                if self.agent_manager:
                    self.agent_manager.release_subtask(task.id, subtask.id, agent_id)
                self._persist_task(task)
                return
            ticket.status = "auto_resolved"
            ticket.resolution = "approve"
            ticket.resolved_at = time.time()

        subtask.finished_at = time.time()
        subtask.actual_seconds = subtask.finished_at - (subtask.started_at or subtask.finished_at)
        subtask.status = "completed"
        if self.agent_manager:
            self.agent_manager.release_subtask(task.id, subtask.id, agent_id)
        self._persist_task(task)

    async def resolve_ticket(self, ticket_id: str, action: str) -> DecisionTicket:
        task, ticket = self._find_ticket(ticket_id)
        if ticket.status != "pending":
            return ticket

        ticket.status = "resolved"
        ticket.resolution = action
        ticket.resolved_at = time.time()

        subtask = task.subtasks[ticket.subtask_id]
        if action.lower() == "approve":
            subtask.status = "ready"
        else:
            subtask.status = "skipped"
            subtask.finished_at = time.time()
            subtask.actual_seconds = 0.0

        if task.status == "waiting_decision":
            task.status = "running"
            self._pause_events[task.id].set()

        self._persist_task(task)
        return ticket

    async def rollback(self, task_id: str, checkpoint_id: str) -> Checkpoint:
        task = self._require_task(task_id)
        checkpoint = next((cp for cp in task.checkpoints if cp.id == checkpoint_id), None)
        if checkpoint is None:
            raise ValueError("checkpoint not found")

        for sid, status in checkpoint.snapshot.items():
            if sid in task.subtasks:
                task.subtasks[sid].status = status
                if status != "completed":
                    task.subtasks[sid].finished_at = None
                    task.subtasks[sid].actual_seconds = None

        for ticket in task.decision_tickets.values():
            if ticket.status == "pending":
                ticket.status = "superseded"

        task.status = "running"
        self._pause_events[task.id].set()
        task.recalculate_progress()
        self._refresh_eta(task)
        self._persist_task(task)
        return checkpoint

    def list_pending_todos(self) -> list[DecisionTicket]:
        tickets: list[DecisionTicket] = []
        for task in self.tasks.values():
            for ticket in task.decision_tickets.values():
                if ticket.status == "pending":
                    tickets.append(ticket)
        tickets.sort(key=lambda t: (int(t.importance_level), t.created_at))
        return tickets

    def _create_checkpoint(self, task: Task, reason: str) -> Checkpoint:
        snapshot = {sid: st.status for sid, st in task.subtasks.items()}
        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            task_id=task.id,
            created_at=time.time(),
            reason=reason,
            snapshot=snapshot,
        )
        task.checkpoints.append(checkpoint)
        self._persist_task(task)
        return checkpoint

    def _refresh_eta(self, task: Task) -> None:
        remaining_est = 0.0
        for st in task.subtasks.values():
            if st.status in {"completed", "skipped"}:
                continue
            if st.status == "running" and st.started_at is not None:
                elapsed = time.time() - st.started_at
                remaining_est += max(0.0, st.estimate_seconds - elapsed)
            else:
                remaining_est += st.estimate_seconds

        uncertainty = 1.15 if task.status == "running" else 1.35
        task.eta_seconds = round(remaining_est * uncertainty, 2)

        completed = [s for s in task.subtasks.values() if s.status in {"completed", "skipped"}]
        confidence = 0.35 + (len(completed) / max(1, len(task.subtasks))) * 0.55
        task.eta_confidence = round(min(0.95, confidence), 2)

    def _estimate_critical_path(self, task: Task) -> int:
        memo: dict[str, int] = {}

        def dfs(sid: str) -> int:
            if sid in memo:
                return memo[sid]
            st = task.subtasks[sid]
            if not st.dependencies:
                memo[sid] = st.estimate_seconds
                return memo[sid]
            best = max(dfs(dep) for dep in st.dependencies)
            memo[sid] = best + st.estimate_seconds
            return memo[sid]

        if not task.subtasks:
            return 0
        return max(dfs(sid) for sid in task.subtasks.keys())

    def _find_ticket(self, ticket_id: str) -> tuple[Task, DecisionTicket]:
        for task in self.tasks.values():
            if ticket_id in task.decision_tickets:
                return task, task.decision_tickets[ticket_id]
        raise ValueError("ticket not found")

    def _require_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("task not found")
        return task

