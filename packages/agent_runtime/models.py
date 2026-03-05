from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional


class ImportanceLevel(IntEnum):
    L0_CORE = 0
    L1_HIGH = 1
    L2_NORMAL = 2
    L3_LOW = 3

    @classmethod
    def from_str(cls, value: str) -> "ImportanceLevel":
        mapping = {
            "L0": cls.L0_CORE,
            "L1": cls.L1_HIGH,
            "L2": cls.L2_NORMAL,
            "L3": cls.L3_LOW,
        }
        try:
            return mapping[value.upper()]
        except KeyError as exc:
            raise ValueError(f"Unsupported importance level: {value}") from exc


@dataclass
class SubTask:
    id: str
    name: str
    estimate_seconds: int
    weight: float
    dependencies: List[str] = field(default_factory=list)
    requires_decision: bool = False
    assigned_agent_id: Optional[str] = None
    status: str = "ready"
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    actual_seconds: Optional[float] = None


@dataclass
class DecisionTicket:
    id: str
    task_id: str
    subtask_id: str
    importance_level: ImportanceLevel
    summary: str
    impact: str
    recommended_action: str
    requires_pause: bool
    status: str = "pending"
    created_at: float = 0.0
    resolved_at: Optional[float] = None
    resolution: Optional[str] = None
    checkpoint_ref: Optional[str] = None


@dataclass
class Checkpoint:
    id: str
    task_id: str
    created_at: float
    reason: str
    snapshot: Dict[str, str]


@dataclass
class Task:
    id: str
    title: str
    goal: str
    created_at: float
    core_pause_level: ImportanceLevel = ImportanceLevel.L0_CORE
    status: str = "queued"
    progress: float = 0.0
    eta_seconds: Optional[float] = None
    eta_confidence: float = 0.2
    planned_seconds: int = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    subtasks: Dict[str, SubTask] = field(default_factory=dict)
    decision_tickets: Dict[str, DecisionTicket] = field(default_factory=dict)
    checkpoints: List[Checkpoint] = field(default_factory=list)
    error: Optional[str] = None

    def runnable_subtasks(self) -> List[SubTask]:
        ready: List[SubTask] = []
        for subtask in self.subtasks.values():
            if subtask.status != "ready":
                continue
            if all(self.subtasks[dep].status == "completed" for dep in subtask.dependencies):
                ready.append(subtask)
        return ready

    def recalculate_progress(self) -> None:
        total_weight = sum(st.weight for st in self.subtasks.values())
        if total_weight <= 0:
            self.progress = 0.0
            return
        done_weight = sum(st.weight for st in self.subtasks.values() if st.status == "completed")
        self.progress = max(0.0, min(1.0, done_weight / total_weight))


def task_to_dict(task: Task) -> dict:
    data = asdict(task)
    data["core_pause_level"] = int(task.core_pause_level)
    for ticket in data["decision_tickets"].values():
        ticket["importance_level"] = int(ticket["importance_level"])
    return data


def task_from_dict(data: dict) -> Task:
    subtasks = {
        sid: SubTask(**subtask_data)
        for sid, subtask_data in data.get("subtasks", {}).items()
    }
    decision_tickets = {}
    for tid, ticket_data in data.get("decision_tickets", {}).items():
        ticket_data = dict(ticket_data)
        ticket_data["importance_level"] = ImportanceLevel(ticket_data["importance_level"])
        decision_tickets[tid] = DecisionTicket(**ticket_data)

    checkpoints = [Checkpoint(**cp) for cp in data.get("checkpoints", [])]

    task_data = dict(data)
    task_data["core_pause_level"] = ImportanceLevel(task_data.get("core_pause_level", 0))
    task_data["subtasks"] = subtasks
    task_data["decision_tickets"] = decision_tickets
    task_data["checkpoints"] = checkpoints
    return Task(**task_data)

