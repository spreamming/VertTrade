# VertTrade Desktop POC

这是 Stage 10 的桌面壳概念验证，**不是正式安装包**，也**不是当前开发重点**。

## 策略说明（2026-07-08）

- 正式 installer 已延后到 **Stage 15**（Stage 11–14 功能完善之后）；
- 日常开发请使用 `scripts/start_local.py` 或 Vite dev server；
- 本目录 POC 保留，用于验证 Electron + FastAPI 路径，无需边开发边重装 installer。

## 目标

- 自动启动 FastAPI 后端；
- 加载 `frontend/dist` 生产前端；
- 用 Electron 打开本地桌面窗口；
- 保持 VertTrade 的个人看盘定位，不引入交易功能。

## 准备

在仓库根目录确保后端依赖已安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

安装前端依赖并构建：

```bash
cd frontend
npm install
npm run build
```

安装桌面壳依赖：

```bash
cd ../desktop
npm install
```

## 启动 POC

```bash
npm run start:poc
```

脚本会先构建前端，然后启动 Electron。Electron 主进程会：

1. 检查 `127.0.0.1:8000` 是否已有后端；
2. 如没有，使用 `.venv` 启动 FastAPI；
3. 加载 `frontend/dist/index.html`；
4. 关闭应用时停止由它启动的后端进程。

## 当前限制

- 还不是 Windows 安装包；
- SQLite 仍使用项目本地配置，尚未迁移到 app data；
- 没有自动更新和签名；
- 后端仍作为 Python sidecar 进程启动；
- 不包含券商登录、下单、自动交易或账户凭证。
