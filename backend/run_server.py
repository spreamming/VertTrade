#!/usr/bin/env python3
"""VertTrade packaged backend entry point for PyInstaller sidecar builds."""
from __future__ import annotations

import os


def main() -> None:
    import multiprocessing

    multiprocessing.freeze_support()

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")

    from backend.app.database import initialize_database

    initialize_database()

    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
