#!/usr/bin/env python3
"""Refresh cached K-line and money-flow data for all watchlist symbols.

Use after market close or when daily bars look stale. This script does not
start a scheduler; run it manually when needed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import SessionLocal
from backend.app.repositories.watchlist_repo import WatchlistRepository
from backend.app.services.stock_service import StockService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh watchlist K-line and money-flow cache from data providers.",
    )
    parser.add_argument(
        "--moneyflow-only",
        action="store_true",
        help="Only refresh money-flow data.",
    )
    parser.add_argument(
        "--kline-only",
        action="store_true",
        help="Only refresh daily K-line data.",
    )
    args = parser.parse_args()

    refresh_kline = not args.moneyflow_only
    refresh_moneyflow = not args.kline_only

    db = SessionLocal()
    try:
        watchlist_repo = WatchlistRepository(db)
        stock_service = StockService(db)
        items = watchlist_repo.list_items()
        if not items:
            print("自选股为空，无需刷新。")
            return 0

        print(f"准备刷新 {len(items)} 只自选股缓存...")
        for item in items:
            code = item.code
            try:
                if refresh_kline:
                    stock_service.get_kline(code, refresh=True)
                    print(f"[K线] {code} 已刷新")
                if refresh_moneyflow:
                    stock_service.get_moneyflow(code, refresh=True)
                    print(f"[资金流] {code} 已刷新")
            except Exception as exc:  # noqa: BLE001 - CLI should continue on per-symbol failure
                print(f"[失败] {code}: {exc}")
        print("刷新完成。")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
