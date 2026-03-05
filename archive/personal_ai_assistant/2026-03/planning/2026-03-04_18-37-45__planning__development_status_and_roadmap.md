# Personal AI Assistant 开发进度与架构能力报告（v0.1）

更新时间：2026-03-04

## 1. 当前总体进度

- 进度阶段：`Phase 1.5`（MVP + 持久化 + 可视化面板）
- 完成度（估算）：
  - 核心执行链路：85%
  - 可视化与交互：65%
  - 安全与治理：40%
  - 可插拔生态：20%
  - 自进化闭环：25%

已实现“可运行闭环”：任务创建 -> DAG 拆解 -> 并发执行 -> 决策分级 -> checkpoint 回退 -> 历史统计 -> 面板展示。

## 2. 组件架构与技术栈

## 2.1 Gateway/API 层

- 路径：`apps/gateway/main.py`
- 技术：`FastAPI + Pydantic`
- 功能：
  - 任务创建、启动、查询
  - 决策票据处理
  - 回退 checkpoint
  - 大盘概览与历史统计接口
  - 静态 UI 托管（`/ui`）

核心接口：

- `POST /tasks`
- `POST /tasks/{task_id}/run`
- `GET /tasks`, `GET /tasks/{task_id}`
- `GET /todo/decisions`
- `POST /tickets/{ticket_id}/resolve`
- `POST /tasks/{task_id}/rollback/{checkpoint_id}`
- `GET /dashboard/overview`, `GET /dashboard/history`

## 2.2 Agent Runtime（规划与调度）

- 路径：
  - `packages/agent_runtime/planner.py`
  - `packages/agent_runtime/scheduler.py`
  - `packages/agent_runtime/models.py`
- 技术：`Python asyncio` 并发协程调度
- 功能：
  - 固定模板 DAG 拆解（6 个子任务）
  - 并发执行（默认并发上限 3）
  - 任务进度计算（基于权重）
  - ETA 与置信度动态更新
  - 决策票据创建与 L0-L3 分级处理
  - checkpoint 快照 + 回退
  - 重启恢复（running -> queued）

## 2.3 Security Policy（决策分级策略）

- 路径：`packages/security_policy/decision.py`
- 技术：轻量策略函数
- 功能：
  - 基于用户核心级别阈值决定是否暂停
  - 当前策略：`ticket_level <= core_pause_level` 即暂停

## 2.4 Observability（统计计算）

- 路径：`packages/observability/metrics.py`
- 技术：内存聚合计算
- 功能：
  - 概览指标：active/completed/failed/avg_progress/mape
  - 历史指标：planned vs actual、绝对误差、误差率

## 2.5 Storage（持久化）

- 路径：`packages/storage/state_store.py`
- 技术：`SQLite`（内置 `sqlite3`）
- 数据模型：
  - 表：`task_state(task_id, payload, updated_at)`
  - 存储方式：每个任务一条 JSON payload（包含 subtasks/tickets/checkpoints）
- 能力：
  - 状态变更即时落盘
  - 启动时全量加载

## 2.6 UI（控制面原型）

- 路径：`apps/gateway/static/index.html`
- 技术：`原生 HTML/CSS/JS`
- 功能：
  - 单入口任务下发
  - 任务列表、状态、进度、ETA
  - 子任务依赖视图（简化 DAG）
  - 待决策 Todo 列表
  - checkpoint 回退
  - 历史耗时展示

## 3. 功能覆盖与能力边界

## 3.1 已实现能力

- 单智能体交互入口
- 任务拆解和并发执行
- L0-L3 决策分级与阻塞规则
- checkpoint 回退
- 预计时间与完成时间统计
- 持久化与重启恢复
- 基础可视化面板

## 3.2 当前能力上限（基于现实现）

说明：以下为“当前代码实现形态”下的工程上限估计，不是理论极限。

- 部署模式：单进程单实例（无分布式）
- 并发执行：每任务默认最多 3 个子任务并发
- 推荐任务规模：
  - 稳定推荐：`<= 500` 历史任务（SQLite JSON 单表）
  - 可运行上限：`~2,000` 任务后查询与全量加载会明显变慢
- 数据体量：
  - 以每任务 10-30KB 状态估算，1,000 任务约 10-30MB
- 响应时延（本地开发机预期）：
  - 常规查询接口通常在毫秒到几十毫秒级
  - 取决于任务数量与 JSON 反序列化成本

## 3.3 关键瓶颈

- 存储为 JSON blob，缺少结构化索引，历史查询扩展性有限。
- 任务状态全内存驻留，进程级故障恢复能力有限。
- 调度器为单机 asyncio，不支持多 worker 分布式调度。
- ETA 目前基于规则估算，无机器学习校准。
- UI 为原型页，未做权限、审计轨迹、复杂拓扑渲染。

## 4. 稳定性与安全现状

已具备：

- 状态持久化与重启恢复（进行中任务恢复为 queued）
- 决策分级暂停机制
- checkpoint 回退

未完成（当前风险点）：

- 无强鉴权（AuthN/AuthZ）
- 无审计不可篡改链
- 无升级双分区（active/candidate）
- 无沙箱隔离（工具执行安全边界）

## 5. 下一步 Roadmap（写入本报告）

## 5.1 R1（1-2 周）：数据与查询可扩展化

目标：让“历史统计 + 大盘筛选”在千级到万级任务仍可用。

- 将 `task_state` JSON 拆分为结构化表：
  - `tasks`, `subtasks`, `decision_tickets`, `task_checkpoints`, `task_metrics`
- 增加索引：`status`, `created_at`, `user_id`, `importance_level`
- API 增加分页与筛选（时间窗口/状态/任务类型）
- 输出容量报告脚本（实时统计 DB 规模与查询耗时）

验收：

- 10,000 任务级别仍可完成分页查询与统计
- 历史面板查询不依赖全量加载

## 5.2 R2（2-4 周）：可插拔组件骨架

目标：把核心能力从“硬编码”升级为“插件加载”。

- 实现插件契约：`manifest + schema + lifecycle`
- 接入插件管理器：install/activate/healthcheck/rollback
- Planner 改为可替换实现（模板版 + LLM 版）
- Tool Runtime 抽象接口（预留 MCP Bridge）

验收：

- 新增一个规划器插件无需改核心代码
- 插件异常可熔断并回滚

## 5.3 R3（3-6 周）：升级不中断与自维护

目标：防止升级卡死或失联。

- 引入 active/candidate 双运行位
- 健康检查通过后切流，失败自动回滚
- 回滚后自动恢复未完成任务到 checkpoint
- 升级事件写入审计

验收：

- 升级失败 5 分钟内自动回退
- 不中断关键任务链路

## 5.4 R4（4-8 周）：智能 ETA 与自进化闭环

目标：让系统“越用越准、越用越会维护自己”。

- 引入 ETA 学习器（按任务类型与历史回归校准）
- 空闲时自反思任务：失败模式分析 -> 候选策略 -> 离线回放
- 新监控项自动提议并进入实验看板
- A/B + 门禁 + 自动回滚

验收：

- ETA 误差（MAPE）持续下降
- 自进化不影响主对话与主任务 SLA

## 6. 推荐下一开发优先级

1. 先做 R1（结构化存储与分页查询）。
2. 紧接 R3（升级不中断），先把“可维护性底座”打牢。
3. 再做 R2/R4，让插件化与自进化建立在稳定底座上。

---

结论：当前系统已经具备“可运行、可观察、可回退”的最小闭环，适合进入“结构化扩展 + 升级安全”阶段。完成 R1+R3 后，才能安全放大到更高任务量级与更复杂自进化能力。
