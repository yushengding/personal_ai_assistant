# Personal AI Assistant Prototype

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn apps.gateway.main:app --reload
```

Open UI:

- `http://127.0.0.1:8000/ui`

## MVP APIs

- `POST /tasks` 创建任务
- `POST /tasks/{task_id}/run` 启动并发执行
- `GET /tasks/{task_id}` 查看任务进度/ETA/子任务状态
- `GET /todo/decisions` 用户待决策列表
- `POST /tickets/{ticket_id}/resolve` 处理 L0 决策票据
- `POST /tasks/{task_id}/rollback/{checkpoint_id}` 回退到快照
- `GET /dashboard/overview` 大盘摘要
- `GET /dashboard/history` 历史预计/实际耗时统计

## Persistence

- SQLite: `data/state.db`
- 启动时自动加载历史任务状态。
- 进程异常重启后，进行中任务会恢复为 `queued`，可继续运行。

## Notes

- 当前为 Phase 1.5 原型：
  - 已有并发执行、ETA、Todo 决策、checkpoint 回退、可视化面板。
  - 下一步可接入真实 LLM Planner、插件系统和权限外置（OPA/OpenFGA）。
