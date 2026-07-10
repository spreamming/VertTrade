#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
SPEC="${ROOT}/scripts/verttrade_backend.spec"
OUT_DIR="${ROOT}/desktop/resources/backend"

if [[ ! -x "$PYTHON" ]]; then
  echo "[失败] 未找到 ${PYTHON}，请先在仓库根目录创建 .venv 并安装 requirements.txt"
  exit 1
fi

echo "[1/3] 安装 PyInstaller..."
"$PYTHON" -m pip install -q pyinstaller

echo "[2/3] 构建 Python sidecar..."
"$PYTHON" -m PyInstaller "$SPEC" --noconfirm --clean --distpath "${ROOT}/dist" --workpath "${ROOT}/build/pyinstaller"

echo "[3/3] 复制到 desktop/resources/backend ..."
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
cp -R "${ROOT}/dist/verttrade-backend/." "$OUT_DIR/"

echo "[完成] sidecar 已输出到 ${OUT_DIR}"
if [[ -x "${OUT_DIR}/verttrade-backend" ]]; then
  echo "可执行文件: ${OUT_DIR}/verttrade-backend"
else
  echo "请检查 dist/verttrade-backend 目录内容。"
fi
