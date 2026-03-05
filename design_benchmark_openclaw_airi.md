# Personal AI Assistant 设计对标：OpenClaw 与 AIRI

## 1. 目标与结论

本文基于本地仓库代码与文档，梳理 `openclaw` 与 `airi` 的设计实现、设计理念、优缺点，并给出后续在 `personal_ai_assistant` 中实现可运行 AI 助理所需的功能与组件蓝图。

核心结论：

- OpenClaw 更像「强工程化的个人代理基础设施」：网关统一、渠道统一、协议统一、安全默认强。
- AIRI 更像「数字角色产品平台」：角色表现力强、跨端体验强、插件与多形态前端丰富。
- 我们后续实现应采用「OpenClaw 的系统骨架 + AIRI 的体验层思想」。

---

## 2. OpenClaw 设计实现梳理

### 2.1 设计理念

- 本地优先（local-first）：一个长期运行的 Gateway 控制全局，默认 `127.0.0.1:18789`。
- 单人助理场景优先：强调 personal assistant，而不是通用 SaaS bot。
- 安全默认优先：配对、鉴权、权限控制、角色策略、owner-only 工具策略。
- 可扩展但收敛：技能/插件扩展能力强，但核心约束明确（避免核心膨胀）。

### 2.2 实现结构（从仓库观察）

- 核心入口：`openclaw/src/index.ts`（CLI 主入口，命令驱动）。
- 网关核心：`openclaw/src/gateway/*`（WS 协议、服务方法、HTTP 面、节点、会话、健康、重载等）。
- 协议层：`openclaw/src/gateway/protocol/index.ts`（TypeBox + AJV 的强类型 schema 体系）。
- Agent 与工具：`openclaw/src/agents/*`（工具策略、沙箱、技能加载、会话管理、工具集）。
- 插件/技能：
  - 插件：`openclaw/src/plugins/*`
  - 技能：`openclaw/docs/tools/skills.md` 与 `openclaw/src/agents/skills/*`
- 文档与运行手册完整：`openclaw/docs/gateway/*`, `openclaw/docs/concepts/*`, `openclaw/docs/tools/*`

### 2.3 优点

- 架构清晰：网关作为唯一控制面，跨渠道/节点/客户端一致。
- 协议严谨：JSON Schema + typed frame，接口可验证、可演进。
- 运维友好：状态、健康、doctor、重载、daemon 化。
- 安全体系完整：鉴权、配对、角色策略、工具权限、默认 DM 安全策略。
- 落地能力强：CLI、Web UI、渠道接入、节点能力（camera/location/canvas）闭环完善。

### 2.4 缺点

- 系统复杂度高：子系统多，学习和维护门槛高。
- 代码面较大：功能强但认知负担重，二次定制成本不低。
- 产品风格偏工程：对“角色化、视觉化、情感体验”支持不是第一优先。

---

## 3. AIRI 设计实现梳理

### 3.1 设计理念

- 目标是“数字生命/虚拟角色容器”：强调人格、陪伴、表现力与互动体验。
- Web 技术优先构建跨端能力：Web/PWA/Desktop/Mobile 多形态统一。
- 前端能力导向：Live2D/VRM/动画/音频/沉浸式 UI 是核心竞争力。
- 平台化演进：多 app + 多 package + provider 抽象 + 插件扩展。

### 3.2 实现结构（从仓库观察）

- Monorepo：`pnpm-workspace.yaml` 覆盖 `apps/ packages/ plugins/ services/ integrations/ docs`。
- 多端应用：
  - `airi/apps/stage-web`
  - `airi/apps/stage-tamagotchi`（Electron）
  - `airi/apps/stage-pocket`（移动端/Capacitor）
- 服务端：`airi/apps/server`
  - 入口 `src/app.ts`（Hono + CORS + auth middleware + 路由注册）
  - 数据 `src/libs/db.ts`（Drizzle + Postgres）
  - 业务层 `src/services/*`（providers/chats/characters）
- 组件调用示例：`airi/apps/component-calling`（组件与 schema 映射，便于 UI/tool 调用）

### 3.3 优点

- 用户体验强：角色展示、动效、模型形态、交互设计成熟度高。
- 跨端思路清晰：Web/桌面/移动并行，便于扩大用户触达。
- 技术栈现代：Vue + TS + Electron + Capacitor + Hono + Drizzle，工程弹性好。
- Provider 适配丰富：对多模型供应商支持广，便于快速试验与切换。

### 3.4 缺点

- “角色产品”重于“系统自治代理”：自动化、控制面、安全策略统一性不如 OpenClaw 强。
- 体系仍在快速演进：部分能力标注 WIP，稳定性和一致性需持续打磨。
- 多端/多包带来构建与协同复杂度，版本与依赖管理压力大。

---

## 4. 对比总结（用于我们选型）

### 4.1 架构取向

- OpenClaw：后端控制面驱动（Gateway-first）。
- AIRI：前端角色体验驱动（Character-first）。

### 4.2 最适合借鉴的部分

- 借鉴 OpenClaw：
  - 网关统一接入
  - 强协议与安全默认
  - 会话/工具/路由治理
- 借鉴 AIRI：
  - 角色化 UI 与多端体验
  - 组件化前端能力
  - provider 抽象与快速实验

### 4.3 建议的融合方向

- 架构底座用 OpenClaw 思路，体验层用 AIRI 思路。
- 第一阶段先做“可靠可用”，第二阶段做“拟人和沉浸”。

---

## 5. 合格好用 AI 助理应具备的功能与功能组件

以下清单可直接作为后续实现 backlog。

### 5.1 对话与任务核心

- 功能：
  - 多轮对话
  - 任务分解与执行
  - 中断、恢复、重试
- 组件：
  - `Conversation Manager`
  - `Task Planner`
  - `Execution Orchestrator`

### 5.2 记忆系统

- 功能：
  - 短期上下文记忆
  - 长期用户偏好记忆
  - 记忆检索与压缩
- 组件：
  - `Session Store`
  - `Memory Store (vector + structured)`
  - `Compaction/Summarizer`

### 5.3 工具调用与自动化

- 功能：
  - 文件、终端、网页、搜索等工具调用
  - 定时任务与事件触发
- 组件：
  - `Tool Registry`
  - `Tool Runtime`
  - `Scheduler (cron/heartbeat/webhook)`

### 5.4 多渠道接入

- 功能：
  - Web、IM、移动端统一接入
  - 同一用户跨端会话连续
- 组件：
  - `Gateway API (WS + HTTP)`
  - `Channel Connectors`
  - `Session Routing`

### 5.5 安全与治理

- 功能：
  - 身份认证与设备配对
  - 高风险操作审批
  - 工具白名单/黑名单
- 组件：
  - `Auth & Pairing`
  - `Policy Engine`
  - `Approval Manager`
  - `Audit Log`

### 5.6 观测与运维

- 功能：
  - 健康检查、日志、成本追踪
  - 配置热更新/回滚
- 组件：
  - `Health Monitor`
  - `Log Pipeline`
  - `Usage/Cost Tracker`
  - `Config Manager`

### 5.7 角色与体验层（可选但强建议）

- 功能：
  - Persona 管理
  - 语音输入输出
  - Live2D/Avatar 展示
- 组件：
  - `Persona Engine`
  - `Voice I/O`
  - `Avatar Renderer`
  - `UX Layer (Desktop/Web/Mobile)`

---

## 6. 面向 `personal_ai_assistant` 的落地架构建议（v1）

### 6.1 v1 目标

- 先实现一个“稳定、可跑、可扩展”的个人 AI 助理最小闭环。

### 6.2 v1 必做模块

- `gateway`：统一 WS/HTTP 控制面
- `agent-runtime`：模型调用 + 工具编排
- `session-memory`：会话存储 + 摘要压缩
- `tooling`：文件、shell、web-search 三类工具
- `security`：基础 auth + 高风险审批
- `client-web`：一个可用的对话与任务界面

### 6.3 v1 技术约束建议

- 所有接口先做 schema 验证（请求、事件、工具参数）。
- 所有工具调用必须带审计记录。
- 所有外部连接（渠道/模型）统一由 gateway 代理，避免直连散落。

---

## 7. 后续执行顺序（建议）

1. 定义统一协议（req/res/event + session + tool-call）。
2. 实现 gateway + 单一 web 客户端闭环。
3. 接入基础 agent runtime（先单模型）。
4. 加入工具系统与审批。
5. 加入 memory（短期->长期）。
6. 最后叠加角色化体验（语音、avatar、多端）。

以上顺序可以最大化“先可用、再好用、最后惊艳”。
