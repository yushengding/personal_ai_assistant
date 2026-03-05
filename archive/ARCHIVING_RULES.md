# 文档归档规则

## 目录规范

- 根路径：`archive/<project>/<YYYY-MM>/<type>/`
- 类型：`analysis | architecture | planning | implementation | operations`

## 命名规范（秒级时间戳）

- 文件名：`YYYY-MM-DD_HH-mm-ss__<type>__<original_name>.md`
- 示例：`2026-03-04_18-37-45__architecture__ai_assistant_architecture_v1.md`

## 归档清单

- 每个批次生成：`manifest.json`
- 字段建议：`project/batch/archived_at/type/relative_path/sha256`
- `archived_at` 使用秒级时间戳：`YYYY-MM-DD_HH-mm-ss`

## 使用方式

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\archive_docs.ps1 -Project personal_ai_assistant -Batch 2026-03 -ArchiveTimestamp 2026-03-04_18-37-45 -CleanExisting
```

参数说明：

- `-ArchiveTimestamp`：指定到秒的归档时间。
- `-CleanExisting`：清理当前批次旧的 `.md` 归档后再写入，避免重复版本。

## 读取建议

1. `architecture`：先读架构约束。
2. `planning`：再读里程碑和验收标准。
3. `analysis`：查看方案背景和调研依据。
4. `implementation`：最后按运行文档复现。
