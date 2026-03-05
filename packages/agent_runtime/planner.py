from __future__ import annotations

from packages.agent_runtime.models import SubTask, Task


def plan_task(task: Task) -> None:
    # A fixed template DAG for MVP. Can be replaced by model planner later.
    template = [
        ("s1", "理解目标并收集上下文", 12, 1.0, [], False),
        ("s2", "拆解方案A", 20, 1.2, ["s1"], False),
        ("s3", "拆解方案B", 18, 1.1, ["s1"], True),
        ("s4", "并发执行A", 28, 1.8, ["s2"], False),
        ("s5", "并发执行B", 30, 1.8, ["s3"], False),
        ("s6", "汇总与验收", 16, 1.3, ["s4", "s5"], True),
    ]

    for sid, name, est, weight, deps, need_decision in template:
        task.subtasks[sid] = SubTask(
            id=sid,
            name=name,
            estimate_seconds=est,
            weight=weight,
            dependencies=deps,
            requires_decision=need_decision,
        )

    task.planned_seconds = sum(st.estimate_seconds for st in task.subtasks.values())
    task.eta_seconds = float(task.planned_seconds)
    task.eta_confidence = 0.55
    task.status = "planning"

