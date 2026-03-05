# Desktop Shell (Electron)

路径：`apps/desktop-shell`

## Dev

```bash
cd apps/desktop-shell
npm install
npm run dev
```

行为：

- Electron 启动后自动拉起 `scripts/run_backend.py`
- 主窗口加载 `http://127.0.0.1:8000/ui`

## Build

```bash
cd apps/desktop-shell
npm run dist
```

输出目录：`apps/desktop-shell/dist`

## Notes

- 当前是 Phase 5 Step-2 脚手架版本。
- 打包产物后续可接入自动更新与安装向导。
- 生产版本建议把 Python 后端打包为 sidecar 可执行文件（PyInstaller）再由 Electron 拉起。
