from datetime import date

import akshare as ak
import pandas as pd
import requests

from ..utils.network import without_system_proxy


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _market_prefix_for_code(code: str) -> str:
    return "sh" if code.startswith("6") else "sz"


def _fetch_daily_kline_tencent(
    code: str,
    start: date,
    end: date,
) -> pd.DataFrame:
    symbol = f"{_market_prefix_for_code(code)}{code}"
    params = {"param": f"{symbol},day,,,1500,qfq"}
    with without_system_proxy():
        response = requests.get(
            "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            params=params,
            timeout=10,
        )
    response.raise_for_status()
    payload = response.json().get("data", {}).get(symbol, {})
    rows = payload.get("qfqday") or payload.get("day") or []
    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)
    frame = frame.iloc[:, :7]
    frame.columns = ["trade_date", "open", "close", "high", "low", "volume", "amount"]
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    frame = frame[(frame["trade_date"] >= start) & (frame["trade_date"] <= end)].copy()
    if frame.empty:
        return frame

    for column in ["open", "close", "high", "low", "volume", "amount"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["amount"] = frame["amount"].fillna(0.0)
    frame["turnover_rate"] = None
    frame["pre_close"] = frame["close"].shift(1)

    return frame[
        [
            "trade_date",
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


def fetch_daily_kline(
    code: str,
    start: date,
    end: date,
    adjust: str = "",
) -> pd.DataFrame:
    try:
        with without_system_proxy():
            frame = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=_format_date(start),
                end_date=_format_date(end),
                adjust=adjust,
            )
    except (requests.RequestException, ValueError):
        return _fetch_daily_kline_tencent(code, start, end)

    if frame.empty:
        return _fetch_daily_kline_tencent(code, start, end)

    renamed = frame.rename(
        columns={
            "日期": "trade_date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turnover_rate",
        }
    )
    renamed["trade_date"] = pd.to_datetime(renamed["trade_date"]).dt.date
    renamed["pre_close"] = renamed["close"].shift(1)

    return renamed[
        [
            "trade_date",
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
