from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Agent:
    agent_id: str
    name: str
    role: str = "general"
    capacity: int = 2
    status: str = "online"
    created_at: float = field(default_factory=time.time)


class AgentManager:
    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self.running: dict[str, set[str]] = {}

    def register(self, agent_id: str, name: str, role: str = "general", capacity: int = 2) -> Agent:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        agent = Agent(agent_id=agent_id, name=name, role=role, capacity=capacity)
        self.agents[agent_id] = agent
        self.running.setdefault(agent_id, set())
        return agent

    def list_agents(self) -> list[dict]:
        rows: list[dict] = []
        for a in self.agents.values():
            used = len(self.running.get(a.agent_id, set()))
            rows.append(
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "capacity": a.capacity,
                    "running": used,
                    "available": max(0, a.capacity - used),
                    "created_at": a.created_at,
                }
            )
        rows.sort(key=lambda x: x["agent_id"])
        return rows

    def has_agents(self) -> bool:
        return len(self.agents) > 0

    def reserve_for_subtask(self, task_id: str, subtask_id: str, preferred_agent_id: Optional[str] = None) -> Optional[str]:
        ticket = f"{task_id}:{subtask_id}"

        if preferred_agent_id:
            agent = self.agents.get(preferred_agent_id)
            if agent and self._has_capacity(preferred_agent_id):
                self.running.setdefault(preferred_agent_id, set()).add(ticket)
                return preferred_agent_id
            return None

        candidates = [a for a in self.agents.values() if a.status == "online" and self._has_capacity(a.agent_id)]
        if not candidates:
            return None

        # Greedy pick: highest free capacity, then lowest current load.
        candidates.sort(
            key=lambda a: (
                -(a.capacity - len(self.running.get(a.agent_id, set()))),
                len(self.running.get(a.agent_id, set())),
                a.agent_id,
            )
        )
        chosen = candidates[0].agent_id
        self.running.setdefault(chosen, set()).add(ticket)
        return chosen

    def release_subtask(self, task_id: str, subtask_id: str, agent_id: Optional[str]) -> None:
        if not agent_id:
            return
        ticket = f"{task_id}:{subtask_id}"
        self.running.setdefault(agent_id, set()).discard(ticket)

    def _has_capacity(self, agent_id: str) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        return len(self.running.get(agent_id, set())) < agent.capacity

