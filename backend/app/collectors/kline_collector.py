from datetime import date

import akshare as ak
import pandas as pd

from ..utils.network import without_system_proxy


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def fetch_daily_kline(
    code: str,
    start: date,
    end: date,
    adjust: str = "",
) -> pd.DataFrame:
    with without_system_proxy():
        frame = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=_format_date(start),
            end_date=_format_date(end),
            adjust=adjust,
        )

    if frame.empty:
        return frame

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
