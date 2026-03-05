# 文档归档索引（personal_ai_assistant）

归档规则：

- 维度：`项目 / 年月 / 类型`
- 命名：`YYYY-MM-DD_HH-mm-ss__type__original_name.md`
- 类型：`analysis | architecture | planning | implementation | operations`
- 标签：在 `manifest.json` 中维护，支持后续检索与复现。

## 当前归档批次

- 项目：`personal_ai_assistant`
- 批次：`2026-03`
- 归档时间戳：`2026-03-04_18-37-45`
- 批次路径：`archive/personal_ai_assistant/2026-03`

## 文件清单

| Type | File | Purpose |
|---|---|---|
| analysis | `analysis/2026-03-04_18-37-45__analysis__ai_assistant_fusion_research_and_design.md` | 融合调研与外部方案分析 |
| analysis | `analysis/2026-03-04_18-37-45__analysis__design_benchmark_openclaw_airi.md` | openclaw/airi 对标分析 |
| architecture | `architecture/2026-03-04_18-37-45__architecture__ai_assistant_architecture_v1.md` | 总体架构目标与分层 |
| architecture | `architecture/2026-03-04_18-37-45__architecture__execution_control_plane_spec_v1.md` | 执行控制面与自维护规范 |
| architecture | `architecture/2026-03-04_18-37-45__architecture__database_and_distribution_strategy.md` | 数据库与分发策略 |
| planning | `planning/2026-03-04_18-37-45__planning__roadmap.md` | 阶段性 roadmap |
| planning | `planning/2026-03-04_18-37-45__planning__development_status_and_roadmap.md` | 开发现状与下一步计划 |
| implementation | `implementation/2026-03-04_18-37-45__implementation__readme.md` | 运行方式与 API 概览 |

## 复现建议

1. 先读 `architecture` 下文档，确认边界与约束。
2. 再读 `planning`，明确阶段目标与验收。
3. 最后按 `implementation/readme` 启动原型验证。
4. 使用同目录 `manifest.json` 做程序化检索（按 type/timestamp/hash）。
