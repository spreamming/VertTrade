const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");

const ROOT_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIST = path.join(ROOT_DIR, "frontend", "dist", "index.html");
const PYTHON_BIN =
  process.platform === "win32"
    ? path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
    : path.join(ROOT_DIR, ".venv", "bin", "python");

let backendProcess = null;

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

async function waitForBackend(timeoutMs = 15000) {
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

  if (!fs.existsSync(PYTHON_BIN)) {
    throw new Error(`未找到 Python 虚拟环境：${PYTHON_BIN}`);
  }

  backendProcess = spawn(
    PYTHON_BIN,
    ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    {
      cwd: ROOT_DIR,
      stdio: "inherit",
    },
  );

  const ready = await waitForBackend();
  if (!ready) {
    throw new Error("后端启动超时，请检查终端日志。");
  }
}

async function createWindow() {
  if (!fs.existsSync(FRONTEND_DIST)) {
    throw new Error("未找到 frontend/dist，请先运行 npm run build:frontend。");
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
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});
