from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from packages.agent_runtime.agent_manager import AgentManager
from packages.agent_runtime.models import Task
from packages.agent_runtime.scheduler import TaskEngine
from packages.avatar.render_store import AvatarRenderStore
from packages.avatar.runtime import build_avatar_runtime_state
from packages.config_center.store import ConfigCenter
from packages.memory.factory import create_memory_store
from packages.operations.upgrade_manager import UpgradeManager
from packages.persona.profile_store import PersonaStore
from packages.observability.factory import create_metrics_sink
from packages.observability.metrics import DashboardMetrics
from packages.plugins.loader import PluginManager
from packages.storage.factory import create_task_store
from packages.voice.factory import create_voice_provider, list_voice_providers


app = FastAPI(title="Personal AI Assistant Gateway", version="0.3.0")
config_center = ConfigCenter(path="configs/database.toml")
agent_manager = AgentManager()


def _init_runtime() -> tuple[Any, Any, Any, TaskEngine]:
    s = create_task_store()
    m = create_memory_store()
    sink = create_metrics_sink()
    eng = TaskEngine(max_parallel_subtasks=3, store=s, agent_manager=agent_manager)
    return s, m, sink, eng


store, memory_store, metrics_sink, engine = _init_runtime()
voice_provider = create_voice_provider()
metrics = DashboardMetrics()
plugin_manager = PluginManager(plugins_root="plugins")
plugin_manager.reload_all()
upgrade_manager = UpgradeManager(state_path="data/upgrade_state.json")
persona_store = PersonaStore(path="data/persona_profile.json")
avatar_render_store = AvatarRenderStore(path="data/avatar_render_config.json")
static_dir = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    core_pause_level: str = Field(default="L0", pattern="^L[0-3]$")


class ResolveTicketRequest(BaseModel):
    action: str = Field(default="approve", pattern="^(approve|reject)$")


class MemoryAddRequest(BaseModel):
    user_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    embedding: list[float] = Field(min_length=1)
    task_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query_embedding: list[float] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    task_id: Optional[str] = None


class UpgradePrepareRequest(BaseModel):
    target_version: str = Field(min_length=1)


class UpgradeRollbackRequest(BaseModel):
    reason: str = Field(default="manual")


class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(default="general", min_length=1)
    capacity: int = Field(default=2, ge=1, le=64)


class AssignSubTaskRequest(BaseModel):
    subtask_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)


class PersonaUpdateRequest(BaseModel):
    name: Optional[str] = None
    style: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    voice_id: Optional[str] = None
    avatar_theme: Optional[str] = None


class VoiceTranscribeRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = Field(default="zh-CN")


class VoiceSpeakRequest(BaseModel):
    text: str = Field(min_length=1)
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class AvatarRenderConfigUpdateRequest(BaseModel):
    renderer: Optional[str] = None
    model_path: Optional[str] = None
    idle_animation: Optional[str] = None
    talk_animation: Optional[str] = None
    emotion_map: Optional[dict[str, str]] = None


def _task_to_dict(task: Task) -> dict[str, Any]:
    data = asdict(task)
    data["core_pause_level"] = f"L{int(task.core_pause_level)}"
    data["subtasks"] = list(data["subtasks"].values())
    data["decision_tickets"] = list(data["decision_tickets"].values())
    for ticket in data["decision_tickets"]:
        ticket["importance_level"] = f"L{int(ticket['importance_level'])}"
    return data


def _reload_runtime() -> dict[str, Any]:
    global store, memory_store, metrics_sink, engine, voice_provider
    store, memory_store, metrics_sink, engine = _init_runtime()
    voice_provider = create_voice_provider()
    return {
        "ok": True,
        "message": "runtime reloaded from configs/database.toml",
        "warning": "in-flight tasks may need manual resume",
    }


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def get_config() -> dict[str, Any]:
    return config_center.load()


@app.post("/config")
def update_config(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        updated = config_center.save(payload)
        metrics_sink.emit("config_updated", {"sections": list(payload.keys())})
        return updated
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/config/reload")
def reload_config_runtime() -> dict[str, Any]:
    try:
        res = _reload_runtime()
        metrics_sink.emit("config_reloaded", res)
        return res
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tasks")
async def create_task(req: CreateTaskRequest) -> dict[str, Any]:
    try:
        task = await engine.create_task(req.title, req.goal, req.core_pause_level)
        metrics_sink.emit("task_created", {"task_id": task.id, "title": task.title})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _task_to_dict(task)


@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str) -> dict[str, Any]:
    try:
        task = await engine.run_task(task_id)
        metrics_sink.emit("task_run_requested", {"task_id": task.id, "status": task.status})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _task_to_dict(task)


@app.get("/tasks")
def list_tasks() -> list[dict[str, Any]]:
    return [_task_to_dict(t) for t in engine.list_tasks().values()]


@app.get("/tasks/query")
def query_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    return store.query_tasks(page=page, page_size=page_size, status=status)


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
        metrics_sink.emit(
            "ticket_resolved",
            {"ticket_id": ticket.id, "task_id": ticket.task_id, "action": req.action, "status": ticket.status},
        )
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
        metrics_sink.emit("task_rollback", {"task_id": task_id, "checkpoint_id": checkpoint_id})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return asdict(checkpoint)


@app.get("/dashboard/overview")
def dashboard_overview() -> dict[str, Any]:
    return metrics.build_overview(engine.list_tasks())


@app.get("/dashboard/history")
def dashboard_history() -> list[dict[str, Any]]:
    return metrics.build_history(engine.list_tasks())


@app.get("/dashboard/history/query")
def dashboard_history_query(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    return store.query_history(page=page, page_size=page_size)


@app.post("/memory/add")
def add_memory(req: MemoryAddRequest) -> dict[str, Any]:
    try:
        entry_id = memory_store.add_entry(
            user_id=req.user_id,
            content=req.content,
            embedding=req.embedding,
            task_id=req.task_id,
            metadata=req.metadata,
        )
        metrics_sink.emit("memory_added", {"entry_id": entry_id, "user_id": req.user_id, "task_id": req.task_id})
        return {"id": entry_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/search")
def search_memory(req: MemorySearchRequest) -> dict[str, Any]:
    try:
        items = memory_store.search(
            user_id=req.user_id,
            query_embedding=req.query_embedding,
            top_k=req.top_k,
            task_id=req.task_id,
        )
        metrics_sink.emit(
            "memory_searched",
            {"user_id": req.user_id, "task_id": req.task_id, "top_k": req.top_k, "hits": len(items)},
        )
        return {"items": items}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/plugins")
def list_plugins() -> dict[str, Any]:
    return {"items": plugin_manager.list_plugins()}


@app.post("/plugins/reload")
def reload_plugins() -> dict[str, Any]:
    plugin_manager.reload_all()
    return {"items": plugin_manager.list_plugins()}


@app.post("/plugins/{name}/activate")
def activate_plugin(name: str) -> dict[str, Any]:
    try:
        return plugin_manager.activate(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/plugins/{name}/deactivate")
def deactivate_plugin(name: str) -> dict[str, Any]:
    try:
        return plugin_manager.deactivate(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/plugins/{name}/health")
def plugin_health(name: str) -> dict[str, Any]:
    try:
        return plugin_manager.healthcheck(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/agents")
def list_agents() -> dict[str, Any]:
    return {"items": agent_manager.list_agents()}


@app.post("/agents/register")
def register_agent(req: AgentRegisterRequest) -> dict[str, Any]:
    try:
        agent = agent_manager.register(
            agent_id=req.agent_id,
            name=req.name,
            role=req.role,
            capacity=req.capacity,
        )
        metrics_sink.emit("agent_registered", {"agent_id": agent.agent_id, "role": agent.role, "capacity": agent.capacity})
        return asdict(agent)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tasks/{task_id}/assign")
def assign_subtask(task_id: str, req: AssignSubTaskRequest) -> dict[str, Any]:
    try:
        result = engine.assign_subtask(task_id=task_id, subtask_id=req.subtask_id, agent_id=req.agent_id)
        metrics_sink.emit("subtask_assigned", result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/dashboard/agents")
def dashboard_agents() -> dict[str, Any]:
    agents = agent_manager.list_agents()
    active_tasks = [t for t in engine.list_tasks().values() if t.status in {"running", "waiting_decision"}]
    return {
        "agents": agents,
        "active_task_count": len(active_tasks),
        "active_subtask_count": sum(
            1 for t in active_tasks for s in t.subtasks.values() if s.status in {"running", "blocked", "ready"}
        ),
    }


@app.get("/dashboard/tasks/{task_id}/dag")
def dashboard_task_dag(task_id: str) -> dict[str, Any]:
    try:
        return engine.task_dag(task_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/persona/profile")
def get_persona_profile() -> dict[str, Any]:
    return asdict(persona_store.load())


@app.post("/persona/profile")
def update_persona_profile(req: PersonaUpdateRequest) -> dict[str, Any]:
    payload = req.model_dump(exclude_none=True)
    profile = persona_store.save(payload)
    metrics_sink.emit("persona_updated", {"updated_fields": list(payload.keys())})
    return asdict(profile)


@app.get("/avatar/state")
def avatar_state() -> dict[str, Any]:
    profile = persona_store.load()
    render_cfg = avatar_render_store.load()
    tasks = list(engine.list_tasks().values())
    current_status = "idle"
    if any(t.status == "waiting_decision" for t in tasks):
        current_status = "waiting_decision"
    elif any(t.status == "running" for t in tasks):
        current_status = "running"
    elif any(t.status == "failed" for t in tasks):
        current_status = "failed"
    elif tasks and all(t.status == "completed" for t in tasks):
        current_status = "completed"

    runtime = build_avatar_runtime_state(current_status, render_cfg.emotion_map or {})
    return {
        "persona_name": profile.name,
        "theme": profile.avatar_theme,
        "renderer": render_cfg.renderer,
        "model_path": render_cfg.model_path,
        "idle_animation": render_cfg.idle_animation,
        "talk_animation": render_cfg.talk_animation,
        "mood": runtime["emotion"],
        "expression": runtime["emotion"],
        "speaking": runtime["speaking"],
        "active_tasks": sum(1 for t in tasks if t.status in {"running", "waiting_decision"}),
    }


@app.get("/avatar/render-config")
def get_avatar_render_config() -> dict[str, Any]:
    return asdict(avatar_render_store.load())


@app.post("/avatar/render-config")
def update_avatar_render_config(req: AvatarRenderConfigUpdateRequest) -> dict[str, Any]:
    payload = req.model_dump(exclude_none=True)
    cfg = avatar_render_store.save(payload)
    metrics_sink.emit("avatar_render_config_updated", {"fields": list(payload.keys())})
    return asdict(cfg)


@app.post("/voice/transcribe")
def voice_transcribe(req: VoiceTranscribeRequest) -> dict[str, Any]:
    result = voice_provider.transcribe(text=req.text, language=req.language)
    metrics_sink.emit(
        "voice_transcribe",
        {"provider": getattr(voice_provider, "name", "unknown"), "chars": len(req.text)},
    )
    return asdict(result)


@app.post("/voice/speak")
def voice_speak(req: VoiceSpeakRequest) -> dict[str, Any]:
    profile = persona_store.load()
    cfg = config_center.load()
    default_voice_id = cfg.get("voice", {}).get("default_voice_id", "airi-cn")
    voice_id = req.voice_id or profile.voice_id or default_voice_id
    result = voice_provider.speak(text=req.text, voice_id=voice_id, speed=req.speed)
    metrics_sink.emit(
        "voice_speak",
        {
            "provider": getattr(voice_provider, "name", "unknown"),
            "voice_id": voice_id,
            "chars": len(req.text),
            "speed": req.speed,
        },
    )
    return asdict(result)


@app.get("/voice/providers")
def voice_providers() -> dict[str, Any]:
    cfg = config_center.load()
    configured = str(cfg.get("voice", {}).get("provider", "mock"))
    return {
        "current": getattr(voice_provider, "name", configured),
        "configured": configured,
        "supported": list_voice_providers(),
    }


@app.get("/voice/health")
def voice_health() -> dict[str, Any]:
    health = voice_provider.healthcheck()
    return asdict(health)


@app.get("/upgrade/status")
def upgrade_status() -> dict[str, Any]:
    return upgrade_manager.status()


@app.post("/upgrade/prepare")
def upgrade_prepare(req: UpgradePrepareRequest) -> dict[str, Any]:
    return upgrade_manager.prepare(req.target_version)


@app.post("/upgrade/healthcheck")
def upgrade_healthcheck() -> dict[str, Any]:
    def check_gateway() -> dict:
        return {"ok": True, "name": "gateway"}

    def check_store() -> dict:
        res = store.query_tasks(page=1, page_size=1)
        return {"ok": True, "name": "store", "sample_total": res.get("total", 0)}

    def check_plugins() -> dict:
        items = plugin_manager.list_plugins()
        unhealthy = [x["name"] for x in items if x.get("health") == "failed"]
        return {"ok": len(unhealthy) == 0, "name": "plugins", "unhealthy": unhealthy}

    return upgrade_manager.healthcheck(
        {
            "gateway": check_gateway,
            "store": check_store,
            "plugins": check_plugins,
        }
    )


@app.post("/upgrade/promote")
def upgrade_promote() -> dict[str, Any]:
    try:
        state = upgrade_manager.promote()
        metrics_sink.emit("upgrade_promoted", state)
        return state
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/upgrade/rollback")
def upgrade_rollback(req: UpgradeRollbackRequest) -> dict[str, Any]:
    state = upgrade_manager.rollback(reason=req.reason)
    metrics_sink.emit("upgrade_rollback", state)
    return state

