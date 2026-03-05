# 当前执行清单（最新版）

更新时间：2026-03-04 22:06:38

## 已完成

- [x] 文档归档体系（秒级时间戳）
- [x] 结构化存储与分页查询（SQLite）
- [x] PostgreSQL store（CRUD/分页/metrics）
- [x] pgvector 记忆检索 API（含 sqlite fallback）
- [x] metrics sink（sqlite/clickhouse）
- [x] 插件契约与插件加载器（MVP）
- [x] 升级不中断底座 MVP（prepare/healthcheck/promote/rollback）
- [x] P2-A baseline：多 Agent 管理后端与基础可视化面板
- [x] P2-B baseline：Persona/Avatar/Voice 接口层
- [x] Phase 5 Step-1：配置中心 API + UI + 运行时重载
- [x] Phase 5 Step-1：一键启动脚本（bat/ps1）
- [x] Phase 5 Step-2：Electron 桌面壳脚手架 + 启动脚本
- [x] Phase 5 Step-3（阶段进展）：Voice Provider 工厂升级（mock/disabled）+ health/providers API
- [x] Phase 5 Step-3（阶段进展）：HttpVoiceProvider（可配置 base_url/model/timeout）接入
- [x] Phase 5 Step-3（阶段进展）：Avatar render-config API 与 runtime 映射联动
- [x] Phase 5 Step-3（阶段进展）：配置中心增加 [voice] 段并接入 UI

## 下一阶段

- [ ] Phase 5 Step-3：真实 ASR/TTS provider（Whisper/Edge-TTS/OpenAI 兼容）接入
- [ ] Phase 5 Step-3：Live2D/WebSocket 渲染桥接（状态+口型）
- [ ] Phase 5 Step-4：安装向导与自动更新
- [ ] Phase 5 Step-5：Python 后端 sidecar 打包（PyInstaller）
