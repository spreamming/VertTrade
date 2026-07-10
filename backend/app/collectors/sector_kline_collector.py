import time

import akshare as ak
import pandas as pd
import requests

from ..utils.network import without_system_proxy
from ..utils.provider_locks import THS_PROVIDER_LOCK
from .sector_collector import SectorDataSourceError, _resolve_eastmoney_board_code


def fetch_sector_kline(name: str, start_date: str | None = None, end_date: str | None = None) -> tuple[pd.DataFrame, str]:
    try:
        frame = _fetch_sector_kline_ths(name, start_date=start_date, end_date=end_date)
        if not frame.empty:
            return frame, "akshare_ths"
    except (requests.RequestException, SectorDataSourceError, ValueError):
        pass

    frame = _fetch_sector_kline_eastmoney(name, start_date=start_date, end_date=end_date)
    if frame.empty:
        raise SectorDataSourceError(f"暂无 {name} 的板块 K 线数据")

    return frame, "eastmoney"


def _fetch_sector_kline_ths(
    name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    start = start_date or "20200101"
    end = end_date or time.strftime("%Y%m%d")
    with THS_PROVIDER_LOCK, without_system_proxy():
        frame = ak.stock_board_industry_index_ths(
            symbol=name,
            start_date=start,
            end_date=end,
        )

    if frame.empty:
        return pd.DataFrame()

    renamed = frame.rename(
        columns={
            "日期": "trade_date",
            "开盘价": "open",
            "最高价": "high",
            "最低价": "low",
            "收盘价": "close",
            "成交量": "volume",
            "成交额": "amount",
        }
    )
    return _normalize_sector_kline_frame(renamed)


def _fetch_sector_kline_eastmoney(
    name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    board_code = _resolve_eastmoney_board_code(name)
    if not board_code:
        return pd.DataFrame()

    params = {
        "secid": f"90.{board_code}",
        "klt": "101",
        "fqt": "1",
        "beg": start_date or "20200101",
        "end": end_date or "20500000",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
    }
    with without_system_proxy():
        response = requests.get(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params=params,
            timeout=10,
        )
    response.raise_for_status()
    rows = response.json().get("data", {}).get("klines", []) or []
    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame([row.split(",") for row in rows])
    frame = frame.iloc[:, :7]
    frame.columns = ["trade_date", "open", "close", "high", "low", "volume", "amount"]
    return _normalize_sector_kline_frame(frame)


def _normalize_sector_kline_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.strftime("%Y-%m-%d")
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["turnover_rate"] = None
    return frame[
        ["trade_date", "open", "high", "low", "close", "volume", "amount", "turnover_rate"]
    ]
