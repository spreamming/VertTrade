# Stage 9 稳定性与桌面打包概念验证

Stage 9 的目标不是继续扩展交易相关功能，而是让当前本地 Web MVP 更稳定、更容易启动，并为后续桌面化做准备。

## 当前稳定性基线

- 后端：FastAPI + SQLite，启动命令为 `uvicorn backend.app.main:app --reload`。
- 前端：Vite dev server，启动命令为 `npm run dev`。
- 本地 launcher：`scripts/start_local.py` 会检查端口、依赖并启动缺失服务。
- 核心验证：
  - `.venv/bin/python -m pytest backend/tests/ -q`
  - `npm run typecheck`
  - `npm run build`

## 数据质量与降级策略

- 历史 K 线、价格位置、资金流和排行榜互相隔离，单个数据源失败不应拖垮整个页面。
- 实时行情是“近实时”，不是交易所 tick 级行情。
- 实时行情响应必须显示：
  - `quote_time`：数据源行情时间
  - `cache_time`：本地刷新/缓存时间
  - `is_stale`：是否为 provider 失败后的缓存回退
  - `cache_age_seconds`：缓存年龄
- 自选股实时刷新只自动刷新前 20 条，避免免费数据源压力过大。

## 桌面打包方向

### Tauri

优点：

- 安装包体积小。
- 适合本地私人工具。
- 前端可继续使用当前 Vite/React。

注意点：

- 需要把 Python/FastAPI 后端作为 sidecar 或改造成本地服务启动流程。
- macOS 权限、签名和路径处理需要额外验证。

### Electron

优点：

- 对“启动本地服务 + 打开前端窗口”的模式更直观。
- Node 生态成熟，打包流程资料多。

注意点：

- 包体积更大。
- 需要明确管理 Python 后端进程生命周期。

## 建议下一步

第一版桌面概念验证建议采用：

1. 继续保留 FastAPI 后端和 Vite 前端。
2. 使用 `scripts/start_local.py` 作为当前本地启动入口。
3. Stage 10 Electron POC 已完成，仅作参考。
4. **正式 installer 延后到 Stage 11–14 功能完善之后（Stage 15）**。

策略调整（2026-07-08）：用户决定功能完善后再打包。打包前重点为实时看盘完善、市场概览、分析体验补全与稳定性验收。

## 本地启动脚本

```bash
.venv/bin/python scripts/start_local.py
```

脚本行为：

- 检查 `.venv/bin/python` 是否存在；
- 检查 `frontend/node_modules` 是否存在；
- 如果 `8000` 未占用，启动 FastAPI 后端；
- 如果 `5173` 未占用，启动 Vite 前端；
- 打印前端和后端 URL；
- `Ctrl+C` 会停止由脚本启动的子进程。

不要在 Stage 9 引入券商登录、下单、自动交易或账户凭证。
