from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from packages.agent_runtime.models import Task
from packages.agent_runtime.scheduler import TaskEngine
from packages.observability.metrics import DashboardMetrics
from packages.storage.state_store import StateStore


app = FastAPI(title="Personal AI Assistant Gateway", version="0.1.0")
store = StateStore(db_path="data/state.db")
engine = TaskEngine(max_parallel_subtasks=3, store=store)
metrics = DashboardMetrics()
static_dir = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    core_pause_level: str = Field(default="L0", pattern="^L[0-3]$")


class ResolveTicketRequest(BaseModel):
    action: str = Field(default="approve", pattern="^(approve|reject)$")


def _task_to_dict(task: Task) -> dict[str, Any]:
    data = asdict(task)
    data["core_pause_level"] = f"L{int(task.core_pause_level)}"
    data["subtasks"] = list(data["subtasks"].values())
    data["decision_tickets"] = list(data["decision_tickets"].values())
    for ticket in data["decision_tickets"]:
        ticket["importance_level"] = f"L{int(ticket['importance_level'])}"
    return data


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tasks")
async def create_task(req: CreateTaskRequest) -> dict[str, Any]:
    try:
        task = await engine.create_task(req.title, req.goal, req.core_pause_level)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _task_to_dict(task)


@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str) -> dict[str, Any]:
    try:
        task = await engine.run_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _task_to_dict(task)


@app.get("/tasks")
def list_tasks() -> list[dict[str, Any]]:
    return [_task_to_dict(t) for t in engine.list_tasks().values()]


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    task = engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return _task_to_dict(task)


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, req: ResolveTicketRequest) -> dict[str, Any]:
    try:
        ticket = await engine.resolve_ticket(ticket_id, req.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ticket_dict = asdict(ticket)
    ticket_dict["importance_level"] = f"L{int(ticket.importance_level)}"
    return ticket_dict


@app.get("/todo/decisions")
def list_todo_decisions() -> list[dict[str, Any]]:
    tickets = engine.list_pending_todos()
    rows: list[dict[str, Any]] = []
    for t in tickets:
        row = asdict(t)
        row["importance_level"] = f"L{int(t.importance_level)}"
        rows.append(row)
    return rows


@app.post("/tasks/{task_id}/rollback/{checkpoint_id}")
async def rollback_task(task_id: str, checkpoint_id: str) -> dict[str, Any]:
    try:
        checkpoint = await engine.rollback(task_id, checkpoint_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return asdict(checkpoint)


@app.get("/dashboard/overview")
def dashboard_overview() -> dict[str, Any]:
    return metrics.build_overview(engine.list_tasks())


@app.get("/dashboard/history")
def dashboard_history() -> list[dict[str, Any]]:
    return metrics.build_history(engine.list_tasks())

