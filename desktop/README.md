# VertTrade Desktop

VertTrade 私人桌面应用（Stage 15）。日常功能开发请优先使用 `scripts/start_local.py`。

## 模式说明

| 命令 | 用途 |
|------|------|
| `npm run start:poc` | 开发机 POC：`.venv` 后端 + 本地 `frontend/dist` |
| `npm run dist:mac` | 构建 macOS DMG（需先构建 sidecar） |
| `npm run dist:win` | 构建 Windows 安装包（需在 Windows 上执行） |

## 快速 POC（开发机）

```bash
# 仓库根目录
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ../desktop
npm install
npm run start:poc
```

## 正式安装包构建

详见 [`docs/stage15_desktop_installer.md`](../docs/stage15_desktop_installer.md)。

```bash
bash scripts/build_backend_sidecar.sh
cd desktop
npm install
npm run dist:mac
```

## 打包后行为

- Electron 启动 PyInstaller sidecar（`resources/backend/verttrade-backend`）
- SQLite 与 `settings.json` 位于系统应用数据目录
- 关闭应用时停止由应用启动的后端进程
- 不包含券商登录、下单、自动交易或账户凭证
