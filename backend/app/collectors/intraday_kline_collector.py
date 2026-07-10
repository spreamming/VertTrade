import requests
import pandas as pd

import akshare as ak

from ..utils.network import without_system_proxy


PERIOD_MAP = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "60m": "60",
}


def _market_symbol(code: str) -> str:
    prefix = "sh" if code.startswith("6") else "sz"
    return f"{prefix}{code}"


def fetch_intraday_kline(code: str, period: str = "1m") -> tuple[pd.DataFrame, str]:
    if period not in PERIOD_MAP:
        raise ValueError("分钟 K 周期仅支持 1m、5m、15m、30m、60m")

    ak_period = PERIOD_MAP[period]
    try:
        with without_system_proxy():
            frame = ak.stock_zh_a_minute(
                symbol=_market_symbol(code),
                period=ak_period,
                adjust="",
            )
    except (requests.RequestException, ValueError):
        return _fetch_intraday_kline_eastmoney(code, ak_period), "eastmoney"

    if frame.empty:
        return _fetch_intraday_kline_eastmoney(code, ak_period), "eastmoney"

    renamed = frame.rename(
        columns={
            "day": "trade_time",
        }
    )
    return _normalize_intraday_frame(renamed), "akshare_sina"


def _secid_for_code(code: str) -> str:
    market = "1" if code.startswith("6") else "0"
    return f"{market}.{code}"


def _fetch_intraday_kline_eastmoney(code: str, period: str) -> pd.DataFrame:
    params = {
        "secid": _secid_for_code(code),
        "klt": period,
        "fqt": "1",
        "beg": "0",
        "end": "20500000",
        "lmt": "1500",
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
    frame.columns = ["trade_time", "open", "close", "high", "low", "volume", "amount"]
    return _normalize_intraday_frame(frame)


def _normalize_intraday_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["trade_time"] = pd.to_datetime(frame["trade_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["pre_close"] = frame["close"].shift(1)
    frame["turnover_rate"] = None
    return frame[
        [
            "trade_time",
            "open",
            "high",
            "low",
            "close",
            "pre_close",
            "volume",
            "amount",
            "turnover_rate",
        ]
    ]
