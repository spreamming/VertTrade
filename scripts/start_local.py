#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
PYTHON = ROOT / ".venv" / "bin" / "python"


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def require_path(path: Path, message: str) -> None:
    if not path.exists():
        print(f"[启动失败] {message}: {path}")
        raise SystemExit(1)


def start_process(command: list[str], cwd: Path, name: str) -> subprocess.Popen:
    print(f"[启动] {name}: {' '.join(command)}")
    return subprocess.Popen(command, cwd=cwd)


def main() -> None:
    require_path(PYTHON, "未找到 Python 虚拟环境，请先创建 .venv 并安装 requirements")
    require_path(FRONTEND / "node_modules", "未找到前端依赖，请先在 frontend 目录运行 npm install")

    processes: list[subprocess.Popen] = []

    if port_is_open(8000):
        print("[已运行] 后端已在 http://127.0.0.1:8000")
    else:
        processes.append(
            start_process(
                [
                    str(PYTHON),
                    "-m",
                    "uvicorn",
                    "backend.app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--reload",
                ],
                ROOT,
                "FastAPI 后端",
            )
        )

    if port_is_open(5173):
        print("[已运行] 前端已在 http://127.0.0.1:5173")
    else:
        processes.append(
            start_process(
                ["npm", "run", "dev", "--", "--host", "127.0.0.1"],
                FRONTEND,
                "Vite 前端",
            )
        )

    print("\nVertTrade 本地启动完成：")
    print("- 前端：http://127.0.0.1:5173")
    print("- 后端：http://127.0.0.1:8000/api/health")
    print("\n按 Ctrl+C 可停止本脚本启动的服务。若端口原本已被占用，本脚本不会停止那些既有服务。")

    if not processes:
        return

    try:
        while True:
            time.sleep(1)
            for process in processes:
                if process.poll() is not None:
                    print(f"[退出] 子进程已结束，退出码 {process.returncode}")
                    raise SystemExit(process.returncode or 0)
    except KeyboardInterrupt:
        print("\n[停止] 正在关闭本脚本启动的服务...")
        for process in processes:
            process.send_signal(signal.SIGINT)
        for process in processes:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
        print("[完成] 已停止。")


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
