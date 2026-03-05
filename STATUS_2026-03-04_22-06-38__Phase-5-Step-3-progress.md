# STATUS_2026-03-04_22-06-38__Phase-5-Step-3-progress

更新时间：2026-03-04 22:06:38
阶段：Phase 5 / Step-3（ASR/TTS 与 Avatar 渲染接入）

## 当前状态

- 网关已切换到 voice provider 工厂实例（支持 runtime reload 后重建 provider）。
- `voice` 模块已提供 provider 抽象健康检查：
  - `mock`：开发调试默认 provider。
  - `disabled`：安全降级 provider。
  - `http`：可配置外部 ASR/TTS 服务（base_url/model/timeout/path）。
- 新增语音可观测 API：
  - `GET /voice/providers`
  - `GET /voice/health`
- `voice_speak` 默认 `voice_id` 选择链路已支持配置中心兜底：
  - request voice_id -> persona voice_id -> config voice.default_voice_id
- Avatar 渲染接入层增强：
  - `GET /avatar/render-config`
  - `POST /avatar/render-config`
  - `GET /avatar/state` 已基于任务态 + emotion_map 计算运行态情绪与 speaking 标志。
- 配置中心新增 `[voice]` 段，并已接入前端配置面板：
  - `provider`
  - `default_voice_id`

## 仍待完成（Step-3）

- 接入真实 ASR provider（优先：Whisper-compatible HTTP）。
- 接入真实 TTS provider（优先：Edge-TTS 或 OpenAI-compatible）。
- 增加 provider 级别超时、重试、熔断与错误码标准化。
- 增加 `avatar` 到前端渲染桥接（WebSocket/事件流）支持口型同步。

## 下一步 TODO（执行顺序）

1. 新增 provider 失败统计写入 metrics sink（按 provider/model/error_code）。
2. 在控制台增加 voice health 卡片与 provider 切换后的在线检查按钮。
3. 设计 Live2D 桥接协议（emotion/speaking/viseme）并落地最小前端演示。
4. 把 http provider 扩展为 openai-compatible/whisper-compatible 双路适配器。
