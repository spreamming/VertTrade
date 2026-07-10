# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPEC).resolve().parent.parent
entry = ROOT / "backend" / "run_server.py"

backend_hidden = collect_submodules("backend.app")

uvicorn_hidden = collect_submodules("uvicorn")

akshare_datas, akshare_binaries, akshare_hidden = collect_all("akshare")

a = Analysis(
    [str(entry)],
    pathex=[str(ROOT)],
    binaries=akshare_binaries,
    datas=akshare_datas,
    hiddenimports=[
        *backend_hidden,
        *uvicorn_hidden,
        *akshare_hidden,
        "multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="verttrade-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="verttrade-backend",
)
