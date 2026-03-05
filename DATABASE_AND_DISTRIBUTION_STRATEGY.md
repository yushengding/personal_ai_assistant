# 数据库与分发策略（v0.1）

更新时间：2026-03-04

## 1. 目标

针对当前系统，新增两类能力：

- 数据侧：引入向量数据库与监控专用数据库，提升检索与可观测性能。
- 体验侧：提供“免命令行配置”的安装体验，同时保留源码运行模式用于调试。

## 2. 多数据库架构建议

## 2.1 按数据类型分层

- 事务与任务主数据（强一致）：`PostgreSQL`
- 向量检索（语义记忆/RAG）：`Qdrant` 或 `PostgreSQL + pgvector`
- 监控/指标/日志（高吞吐时序分析）：`ClickHouse` 或 `OpenSearch/Elastic`
- 缓存与队列（实时状态）：`Redis`（可选）

## 2.2 为什么不把所有数据都放一个库

- 任务状态和审批要强一致，适合关系型事务库。
- 向量检索强调 ANN 索引与过滤能力，适合向量引擎。
- metrics/logs/traces 是高吞吐时序数据，适合列式或搜索引擎。

单库方案可以快起步，但随着任务量增长会很快遇到性能和成本拐点。

## 3. 向量数据库选型

## 3.1 方案 A：PostgreSQL + pgvector（优先起步）

适用：先快落地、运维简单、数据一致性优先。

优点：

- 与事务数据同库，开发成本低。
- 支持向量近邻查询与 SQL 联查。
- 容易做权限、审计、备份统一治理。

边界：

- 大规模高并发 ANN 检索时，需要额外索引/参数调优。

参考：

- pgvector 官方仓库：https://github.com/pgvector/pgvector

## 3.2 方案 B：Qdrant（向量能力优先）

适用：语义检索是核心、需要高性能过滤与向量功能迭代。

优点：

- 原生向量数据库，支持 payload 过滤与复合检索。
- 适合记忆系统、知识库检索、工具调用语义路由。

边界：

- 需要引入额外组件，数据同步链路要设计好。

参考：

- Concepts: https://qdrant.tech/documentation/concepts/
- Payload: https://qdrant.tech/documentation/concepts/payload/
- Filtering: https://qdrant.tech/documentation/concepts/filtering/

## 3.3 方案 C：Elasticsearch 向量能力（检索+观测一体）

适用：已经使用 Elastic 生态，想统一搜索与 observability。

优点：

- `dense_vector + knn` 可直接做向量查询。
- 与日志/指标/追踪生态联动方便。

边界：

- 作为纯向量检索引擎时，成本和调优复杂度通常高于专用向量库。

参考：

- Vector docs: https://www.elastic.co/docs/solutions/search/vector
- Dense vector: https://www.elastic.co/guide/en/elasticsearch/reference/current/dense-vector.html/

## 4. 监控与 Metrics 数据库选型

## 4.1 ClickHouse（推荐用于高吞吐 metrics/logs）

适用：高写入、高基数、重分析查询。

优点：

- 列式分析性能强，适合时间序列与聚合。
- 对大规模事件数据成本效率高。

参考：

- Use cases: https://clickhouse.com/use-cases
- Observability: https://clickhouse.com/use-cases/observability

## 4.2 OpenSearch / Elastic（推荐用于日志检索与可视化生态）

适用：需要成熟搜索体验、告警、可视化生态。

优点：

- 日志检索和故障排查体验成熟。
- 与 OpenTelemetry/OTLP 兼容路径明确。

参考：

- OpenSearch Observability: https://docs.opensearch.org/platform/observability/
- Elastic OTel intake: https://www.elastic.co/docs/solutions/observability/apm/opentelemetry-intake-api

## 4.3 本项目建议（分阶段）

- P0：继续 `SQLite`（本地原型）
- P1：迁移 `PostgreSQL`（主数据） + `pgvector`（向量）
- P2：新增 `ClickHouse`（metrics）
- P3：如需强日志检索/告警生态，再引入 `OpenSearch` 或 `Elastic`

## 5. 能力量级建议（工程目标）

- PostgreSQL 主数据：10^5~10^7 任务记录（按索引与分区设计）
- pgvector/Qdrant：10^6~10^8 向量（视维度、召回率、硬件）
- ClickHouse 监控事件：10^8~10^10 级事件（列式压缩 + 分区）

说明：具体上限取决于 embedding 维度、保留周期、硬件和索引参数。

## 6. 安装与分发策略（零命令行优先）

## 6.1 目标体验

- 用户下载后“双击安装即可使用”。
- 首次启动用 GUI 向导完成配置，不要求手动设置环境变量。
- 仍提供源码运行模式，方便开发调试。

## 6.2 桌面安装包方案

推荐两条路线：

- 路线 1：`Tauri`（轻量、安装包体积更小）
- 路线 2：`Electron + electron-builder`（生态成熟、自动更新能力成熟）

参考：

- Tauri distribute: https://v2.tauri.app/distribute/
- electron-builder: https://www.electron.build/

## 6.3 Python 后端打包

- 使用 `PyInstaller` 将 Python 服务打包为可执行文件，作为桌面壳的 sidecar。
- 应用启动时自动拉起本地服务并进行健康检查。

参考：

- PyInstaller: https://pyinstaller.org/

## 6.4 配置与密钥管理

- 不再要求用户手动设置 shell 环境变量。
- 改为 GUI 设置页写入本地配置库（加密存储）。
- 支持配置导入/导出与多 profile（个人/工作）。

## 6.5 源码运行模式（开发者）

- Python：`uv` 管理环境与依赖。
- 前端：`node/pnpm` 启动。

参考：

- uv docs: https://docs.astral.sh/uv/

## 7. 推荐落地决策

- 近期（2-4 周）：`PostgreSQL + pgvector`，快速统一主数据与向量能力。
- 中期（4-8 周）：引入 `ClickHouse` 承担 metrics，降低观测查询压力。
- 分发：优先 `Tauri + PyInstaller sidecar`，并保留 `uv + node` 的源码运行链路。

## 8. 下一步实施清单（可直接开发）

1. 将 SQLite 模型迁移为 PostgreSQL 结构化表。
2. 接入 pgvector，并落地记忆检索 API。
3. 设计 metrics 事件 schema，并在 ClickHouse 建表。
4. 实现 GUI 配置中心（替代环境变量）。
5. 构建桌面安装包（Tauri 或 Electron）与自动更新流程。
6. 维护一套源码开发脚本（uv + node）与调试文档。
