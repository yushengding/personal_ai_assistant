# AI Assistant Roadmap（最新版）

更新时间：2026-03-04 22:06:38

## 目标

在 OpenClaw（工程控制面）与 AIRI（交互体验面）融合基础上，落地可插拔、可维护、可视化、可自进化且升级不中断的个人 AI Assistant。

## Phase 0：架构对齐（已完成）

- 融合设计文档、执行控制面规范、安全边界。
- 定义 KPI、风险与回滚策略。

## Phase 1：可运行 MVP（已完成）

- 单入口交互、任务拆解并发执行、进度与 ETA。
- DecisionTicket 分级、checkpoint 回退、基础看板。

## Phase 2：工程化底座与平台能力（进行中）

### P2-Core（已完成）

- 插件契约 + 插件加载器（MVP）
- SQLite 结构化存储 + 分页查询
- PostgreSQL store（CRUD/分页/metrics）
- pgvector 记忆检索 API（含 sqlite fallback）
- metrics sink（sqlite/clickhouse 可切换）

### P2-S（下一优先）：升级不中断底座

范围：

- Active/Candidate 双槽位
- 升级健康检查与自动回滚
- 未完成任务恢复策略（基于 checkpoint）

验收：

- 升级失败 5 分钟内自动回退
- 升级过程主任务不中断

### P2-A：多 Agent 并发可视化管理

范围：

- 多 Agent 泳道视图
- 任务 DAG 图、关键路径、阻塞节点
- 并发资源配额面板（agent/tool/model）
- 任务接管、重试、暂停、回退操作

验收：

- 同时管理多任务/多 agent 状态
- 支持按用户、任务类型、状态筛选
- 可追踪每个子任务 ETA 与依赖关系

### P2-B：AIRI 风格交互层（皮套人）

范围：

- Persona 管理
- Avatar/Live2D 渲染接入层
- 语音输入输出（ASR/TTS）
- 角色态交互与任务态控制面联动

验收：

- 用户可通过角色化 UI 下发任务
- 角色态与任务执行态状态一致
- 角色模块可插拔、不影响核心执行链路

## Phase 3：自进化与治理增强

- 空闲自反思 -> 候选策略 -> 离线回放 -> 小流量发布
- 实验监控项自动提议与晋升
- 策略门禁（质量/成本/安全）

## Phase 4：高级能力

- MCP Bridge
- Durable Execution（Temporal/LangGraph）
- 高风险执行强隔离（gVisor/Firecracker）

## Phase 5：分发与开箱体验

- 零命令行安装包（Tauri/Electron）
- GUI 配置中心（替代手工环境变量）
- 源码模式保留（uv + node）

阶段进展（Step-3 in progress）：

- Voice Provider 工厂升级（`mock` / `disabled`）与 runtime reload 打通
- `/voice/providers` 与 `/voice/health` 接口已上线
- `/avatar/render-config` 与 `/avatar/state` 渲染配置联动完成

## 当前执行顺序（明确）

1. P2-S：升级不中断底座（已完成 MVP）
2. P2-A：多 Agent 并发可视化管理（已完成 baseline）
3. P2-B：AIRI 风格皮套人交互层（已完成接口层 baseline）
4. Phase 5：安装包与 GUI 配置中心（当前优先，Step-3 进行中）
