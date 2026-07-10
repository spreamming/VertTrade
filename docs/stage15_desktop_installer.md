# Stage 15 桌面安装包

Stage 15 将 VertTrade 从「本地 Web + 启动脚本」升级为可双击使用的私人桌面应用。

## 交付物

- **macOS**：`desktop/dist/VertTrade-<version>-mac.dmg`（及 zip）
- **Windows**：`desktop/dist/VertTrade Setup <version>.exe`（NSIS，需在 Windows 上构建）
- **Python sidecar**：PyInstaller 打包的 FastAPI 后端，不再依赖仓库 `.venv`
- **SQLite**：写入应用数据目录，而非项目 `data/` 目录

## 数据目录

| 平台 | 默认路径 |
|------|----------|
| macOS | `~/Library/Application Support/VertTrade/` |
| Windows | `%APPDATA%/VertTrade/` |
| Linux | `~/.local/share/VertTrade/` |

Electron 启动时会设置 `VERTTRADE_DATA_DIR=<userData>`，其中包含：

- `market_watch.db` — 自选股、K 线缓存、资金流缓存
- `settings.json` — 可选本地设置（见下）

### settings.json 示例

```json
{
  "watchlist_live_refresh_limit": 20
}
```

## 构建步骤（macOS 示例）

在仓库根目录：

```bash
# 1. 后端依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 前端生产构建
cd frontend && npm install && npm run build && cd ..

# 3. 桌面依赖
cd desktop && npm install && cd ..

# 4. 构建 Python sidecar（输出到 desktop/resources/backend/）
bash scripts/build_backend_sidecar.sh

# 5. 生成安装包
cd desktop
npm run dist:mac
```

产物位于 `desktop/dist/`。

## 开发模式 vs 安装包

| 模式 | 启动方式 | 后端 | 数据库 |
|------|----------|------|--------|
| 日常开发 | `scripts/start_local.py` | `.venv` + uvicorn | `data/market_watch.db` |
| Desktop POC | `cd desktop && npm run start:poc` | `.venv` + uvicorn | `data/market_watch.db` |
| 正式安装包 | 双击 VertTrade.app | PyInstaller sidecar | Application Support |

**边开发边功能迭代时，请继续用 `start_local.py`，不要每次改代码都重装 DMG。**

## 更新流程（个人使用）

1. 拉取新版本代码
2. 重新执行上述构建步骤
3. 双击新 DMG / 安装程序，**覆盖安装**
4. 应用数据目录中的 SQLite 会保留（路径不变）

当前 **未实现** 自动更新服务器或签名公证（个人使用可后置）。

## 验收清单

- [ ] 双击安装包可打开，无需终端
- [ ] `/api/health` 返回 `packaged: true` 与正确 `data_dir`
- [ ] 添加自选股后重启应用，数据仍在
- [ ] 覆盖安装后数据仍在
- [ ] 无券商登录、下单、自动交易入口

## 已知限制

- 前端构建必须设置 Vite `base: './'`；若使用绝对路径 `/assets/...`，Electron 白屏
- 首次 sidecar 构建较慢，且依赖 PyInstaller 对 AKShare 的完整收集
- Windows 安装包需在 Windows 环境构建
- macOS 未签名应用首次打开可能需「仍要打开」
- 后端 stdout 在打包模式下写入 pipe，排错时可临时改 `main.cjs` 的 `stdio`

## 非交易边界

与全项目一致：不包含券商 API、下单、账户凭证或自动交易。
