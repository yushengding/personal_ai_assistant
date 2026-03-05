# Personal AI Assistant Prototype

## Quick Start (No manual env vars)

### Option A: Web app one-click start

- BAT: `scripts/start_app.bat`
- PowerShell: `scripts/start_app.ps1`

### Option B: Desktop shell one-click start (Electron)

- BAT: `scripts/start_desktop.bat`
- PowerShell: `scripts/start_desktop.ps1`

Desktop shell docs:

- `apps/desktop-shell/README.md`

## Config Center (GUI + API)

UI 顶部已提供配置中心：

- 数据后端：sqlite/postgres
- 向量后端：pgvector/qdrant（当前实现 pgvector + sqlite fallback）
- metrics 后端：sqlite/clickhouse
- 语音后端：mock/http/disabled
- 保存后可点击“重载运行时”

API：

- `GET /config`
- `POST /config`
- `POST /config/reload`

配置文件：`configs/database.toml`

## Storage Backend Selection

- `driver = "sqlite"` 使用 SQLite
- `driver = "postgres"` 使用 PostgreSQL

PostgreSQL 依赖安装：

```bash
pip install -r requirements-postgres.txt
```

## Metrics Backend Selection

- `backend = "sqlite"` 使用 SQLite metrics sink
- `backend = "clickhouse"` 使用 ClickHouse sink

ClickHouse 依赖安装：

```bash
pip install -r requirements-clickhouse.txt
```

ClickHouse 建表：

- `migrations/clickhouse/001_metrics_events.sql`

## Vector Memory

- `POST /memory/add`
- `POST /memory/search`

SQLite fallback:

- `packages/memory/sqlite_memory_store.py`

PostgreSQL + pgvector:

- `migrations/postgresql/002_pgvector_memory.sql`
- `packages/memory/pgvector_memory_store.py`

## Plugin System (MVP)

- `GET /plugins`
- `POST /plugins/reload`
- `POST /plugins/{name}/activate`
- `POST /plugins/{name}/deactivate`
- `GET /plugins/{name}/health`

## Multi-Agent Management (P2-A baseline)

- `POST /agents/register`
- `GET /agents`
- `POST /tasks/{task_id}/assign`
- `GET /dashboard/agents`
- `GET /dashboard/tasks/{task_id}/dag`

## AIRI-style Persona Layer (P2-B baseline)

- `GET /persona/profile`
- `POST /persona/profile`
- `GET /avatar/state`
- `GET /avatar/render-config`
- `POST /avatar/render-config`
- `POST /voice/transcribe`
- `POST /voice/speak`
- `GET /voice/providers`
- `GET /voice/health`

## Upgrade Control Plane (MVP)

- `GET /upgrade/status`
- `POST /upgrade/prepare`
- `POST /upgrade/healthcheck`
- `POST /upgrade/promote`
- `POST /upgrade/rollback`

## Core APIs

- `POST /tasks`
- `POST /tasks/{task_id}/run`
- `GET /tasks/{task_id}`
- `GET /tasks/query?page=1&page_size=20&status=running`
- `GET /todo/decisions`
- `POST /tickets/{ticket_id}/resolve`
- `POST /tasks/{task_id}/rollback/{checkpoint_id}`
- `GET /dashboard/overview`
- `GET /dashboard/history/query?page=1&page_size=50`

## Capacity Report

```bash
python tools/capacity_report.py
```

## Status Snapshot

- `STATUS_2026-03-04_19-46-56__Phase-1.6_to_Phase-2.0.md`
- `PLAN_2026-03-04_20-15-45__P2S_P2A_P2B.md`
- `STATUS_2026-03-04_22-06-38__Phase-5-Step-3-progress.md`

## Notes

- 当前已完成 P2-S / P2-A baseline / P2-B baseline / Phase5 Step-1~Step-2。
- 当前优先：Phase5 Step-3（真实语音与皮套人渲染接入）。
