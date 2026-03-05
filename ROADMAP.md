# AI Assistant Roadmap（基于现有设计文档）

更新时间：2026-03-04

## 目标

在 OpenClaw（工程控制面）与 AIRI（交互体验面）融合基础上，落地一个可插拔、可维护、可视化、可自进化且升级不中断的个人 AI Assistant。

## Phase 0：架构对齐（已完成）

- 完成融合设计文档、执行控制面规范、安全与成长边界定义。
- 输出分阶段目标、KPI、风险与回滚策略。

验收：文档完整、可直接驱动工程实现。

## Phase 1：可运行 MVP（1-2 周）

### 范围

- 单入口智能体交互（API 形态，后续接 AIRI 风格前端）。
- 任务拆解（DAG）与并发执行。
- 实时进度与 ETA。
- DecisionTicket 分级（L0-L3）与用户 Todo。
- Checkpoint 生成与回退。
- 监控大盘基础指标与历史任务时间统计。

### 交付

- `apps/gateway`：FastAPI 网关与 REST 接口。
- `packages/agent_runtime`：Planner + Scheduler + Checkpoint。
- `packages/security_policy`：决策分级与暂停策略。
- `packages/observability`：大盘统计计算。

### 验收

- 支持并发执行与关键路径可视化数据输出。
- 所有历史任务可查看预计时间、完成时间、误差。
- L0 级决策自动暂停，L1-L3 自动决策并保留回退点。

## Phase 2：可维护与可插拔（2-4 周）

### 范围

- 插件契约（manifest/schema/lifecycle）。
- 插件加载器与健康检查。
- 策略引擎外置化（可接 OPA/OpenFGA）。
- 持久化与审计增强（数据库迁移、索引、归档）。

### 验收

- 新增工具插件不改核心代码。
- 策略可热更新，异常可 5 分钟内回滚。

## Phase 3：升级不中断与自进化（4-8 周）

### 范围

- Active/Candidate 双分区升级与灰度切换。
- 空闲时自反思：失败模式挖掘、策略候选生成、离线回放验证。
- 自动新增“实验监控项”，验证通过后纳入正式看板。

### 验收

- 升级失败不丢任务、不失联、自动回滚。
- 学习任务不影响主链路 SLA。

## Phase 4：高级能力（8 周+）

### 范围

- MCP Bridge。
- Durable Execution（Temporal 或 LangGraph）。
- 高风险执行隔离强化（gVisor / Firecracker）。

### 验收

- 跨天任务可稳定恢复。
- 多租户高风险任务具备强隔离保障。

## Phase 5：数据平台与分发体验（并行推进）

### 范围

- 数据层升级：`PostgreSQL + pgvector`，并规划 `ClickHouse` 承担 metrics。
- 日志/检索平台：评估 `OpenSearch / Elastic`（按观测需求决定）。
- 零命令行安装：桌面安装包（Tauri 或 Electron）。
- 保留源码模式：`uv + node` 调试链路。

### 验收

- 普通用户可通过安装包开箱即用（无需手动环境变量配置）。
- 开发者可 10 分钟内通过源码模式启动完整服务。
- 历史任务与指标查询性能显著优于 SQLite 原型。

## 当前迭代计划（本次编码后）

1. R1：将 SQLite JSON 存储升级为 PostgreSQL 结构化表。
2. R2：接入 pgvector 记忆检索能力。
3. R3：引入 metrics 专用存储（ClickHouse）。
4. R4：桌面安装包与 GUI 配置中心。
5. R5：保留并完善源码调试链路（uv + node）。
