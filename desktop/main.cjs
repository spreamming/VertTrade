const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");

const ROOT_DIR = path.resolve(__dirname, "..");
const IS_PACKAGED = app.isPackaged;
const USER_DATA_DIR = app.getPath("userData");
const FRONTEND_DIST = IS_PACKAGED
  ? path.join(process.resourcesPath, "frontend", "index.html")
  : path.join(ROOT_DIR, "frontend", "dist", "index.html");

const DEV_PYTHON_BIN =
  process.platform === "win32"
    ? path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
    : path.join(ROOT_DIR, ".venv", "bin", "python");

let backendProcess = null;
let backendStartedByApp = false;

function resolveBackendCommand() {
  if (!IS_PACKAGED) {
    if (!fs.existsSync(DEV_PYTHON_BIN)) {
      throw new Error(`未找到 Python 虚拟环境：${DEV_PYTHON_BIN}`);
    }
    return {
      command: DEV_PYTHON_BIN,
      args: ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
      cwd: ROOT_DIR,
    };
  }

  const backendDir = path.join(process.resourcesPath, "backend");
  const binaryName = process.platform === "win32" ? "verttrade-backend.exe" : "verttrade-backend";
  const binaryPath = path.join(backendDir, binaryName);
  if (!fs.existsSync(binaryPath)) {
    throw new Error(`未找到打包后端：${binaryPath}`);
  }
  return {
    command: binaryPath,
    args: [],
    cwd: backendDir,
  };
}

function backendEnvironment() {
  return {
    ...process.env,
    VERTTRADE_DATA_DIR: USER_DATA_DIR,
    VERTTRADE_PACKAGED: IS_PACKAGED ? "1" : "0",
    APP_ENV: IS_PACKAGED ? "production" : process.env.APP_ENV || "development",
    PORT: "8000",
    HOST: "127.0.0.1",
  };
}

function portIsOpen(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    socket.setTimeout(700);
    socket.on("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.on("error", () => resolve(false));
  });
}

async function waitForBackend(timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await portIsOpen(8000)) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  return false;
}

async function startBackendIfNeeded() {
  if (await portIsOpen(8000)) {
    return;
  }

  const { command, args, cwd } = resolveBackendCommand();
  backendProcess = spawn(command, args, {
    cwd,
    env: backendEnvironment(),
    stdio: IS_PACKAGED ? "pipe" : "inherit",
  });
  backendStartedByApp = true;

  backendProcess.on("exit", (code, signal) => {
    if (!backendStartedByApp) {
      return;
    }
    backendStartedByApp = false;
    if (code && code !== 0) {
      dialog.showErrorBox(
        "VertTrade 后端已退出",
        `后端进程异常结束（code=${code ?? "null"}, signal=${signal ?? "null"}）。`,
      );
    }
  });

  const ready = await waitForBackend();
  if (!ready) {
    throw new Error("后端启动超时，请检查 sidecar 日志或端口 8000 是否被占用。");
  }
}

async function createWindow() {
  if (!fs.existsSync(FRONTEND_DIST)) {
    throw new Error(
      IS_PACKAGED
        ? "未找到打包前端资源。"
        : "未找到 frontend/dist，请先运行 npm run build:frontend。",
    );
  }

  const win = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 760,
    title: "VertTrade",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  await win.loadFile(FRONTEND_DIST);
}

app.whenReady().then(async () => {
  try {
    fs.mkdirSync(USER_DATA_DIR, { recursive: true });
    await startBackendIfNeeded();
    await createWindow();
  } catch (error) {
    dialog.showErrorBox("VertTrade 启动失败", error.message);
    app.quit();
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  backendStartedByApp = false;
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});
