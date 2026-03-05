# ASSET_TODO_2026-03-04_22-16-21__Phase-5-Step-3.md

更新时间：2026-03-04 22:16:21
项目：personal_ai_assistant
阶段：Phase 5 / Step-3（进行中）

## 一、现有资产梳理

### 1) 架构与核心能力

- Gateway（FastAPI）统一入口：任务、监控、配置、插件、升级、persona/avatar/voice。
- Task Engine：任务拆解、并发执行、checkpoint、决策票据（DecisionTicket）、回滚。
- Multi-Agent baseline：agent 注册、子任务分配、并发状态面板、DAG 查询。
- Upgrade Manager（MVP）：prepare/healthcheck/promote/rollback，保障升级可回退。

### 2) 数据与存储资产

- SQLite 结构化存储：任务、历史、分页查询、统计查询。
- PostgreSQL store：同构 CRUD/分页/metrics。
- 向量记忆：pgvector 主实现 + sqlite fallback。
- Metrics Sink：sqlite / clickhouse 可切换。

### 3) 交互与可视化资产

- 控制台 UI（`apps/gateway/static/index.html`）：
  - 大盘 KPI（Active/Completed/Failed/Avg Progress/MAPE）
  - 任务列表、DAG 视图、Todo 决策区
  - Agent 管理面板
  - 配置中心（database/vector/metrics/voice）
- Persona/Avatar/Voice 接口层：
  - Persona：`GET/POST /persona/profile`
  - Avatar：`GET /avatar/state`、`GET/POST /avatar/render-config`
  - Voice：`POST /voice/transcribe`、`POST /voice/speak`、`GET /voice/providers`、`GET /voice/health`

### 4) 语音与皮套人资产（Step-3 进展）

- Voice Provider 抽象与工厂已完成，支持：`mock` / `disabled` / `http`。
- `HttpVoiceProvider` 支持 `base_url/api_key/model/timeout/path` 配置。
- Avatar runtime 支持根据任务状态 + emotion_map 输出情绪和 speaking 标志。

### 5) 分发与工程资产

- 一键启动脚本：`scripts/start_app.bat`、`scripts/start_app.ps1`。
- 桌面壳脚手架：`apps/desktop-shell` + `scripts/start_desktop.*`。
- 配置中心：`packages/config_center/store.py` + `configs/database.toml`（含 `[voice]`）。
- 归档文档体系：秒级时间戳命名的 PLAN/STATUS/TODO 文档。

### 6) 关键文档资产

- `ROADMAP.md`
- `TODO_NOW.md`
- `STATUS_2026-03-04_22-06-38__Phase-5-Step-3-progress.md`
- `README.md`

## 二、下一阶段 TODO（最新版）

### P0（当前冲刺，Phase 5 Step-3）

1. 接入真实 ASR provider（Whisper/OpenAI-compatible）。
2. 接入真实 TTS provider（Edge-TTS/OpenAI-compatible）。
3. 增加 provider 级别重试/超时/错误码标准化。
4. 增加 voice 失败统计写入 metrics（provider/model/error_code）。
5. 增加 Live2D/WebSocket 渲染桥接（emotion/speaking/viseme）。
6. 控制台新增 voice health 卡片与在线检测按钮。

### P1（Step-4）

1. 安装向导（GUI）与依赖自检。
2. 自动更新策略（含健康检查与回滚联动）。
3. 桌面壳集成后端生命周期管理（启动、停止、日志查看）。

### P2（Step-5）

1. Python 后端 sidecar 打包（PyInstaller）。
2. 首次启动初始化（数据库、配置、插件扫描）。
3. 发布版 smoke 测试与容量基线测试。

## 三、执行建议（短期）

- 先做“真实 ASR/TTS provider + 指标打点”，再做“Live2D 桥接最小演示”。
- 完成后立即补一轮端到端 smoke（任务流 + 语音流 + 配置重载 + 回滚）。
