import akshare as ak
import pandas as pd

from ..utils.network import without_system_proxy


class MoneyflowDataSourceError(RuntimeError):
    pass


REQUIRED_COLUMNS = {
    "日期",
    "主力净流入-净额",
    "主力净流入-净占比",
    "超大单净流入-净额",
    "大单净流入-净额",
    "中单净流入-净额",
    "小单净流入-净额",
}


def market_code_for_stock(code: str, exchange: str | None = None) -> str:
    if exchange:
        return "sh" if exchange.upper() == "SH" else "sz"
    if code.startswith("6"):
        return "sh"
    return "sz"


def fetch_stock_moneyflow(code: str, exchange: str | None = None) -> pd.DataFrame:
    market = market_code_for_stock(code, exchange)
    with without_system_proxy():
        frame = ak.stock_individual_fund_flow(stock=code, market=market)

    if frame.empty:
        return frame

    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing = "、".join(sorted(missing_columns))
        raise MoneyflowDataSourceError(f"资金流数据源缺少字段：{missing}")

    renamed = frame.rename(
        columns={
            "日期": "trade_date",
            "主力净流入-净额": "main_net_inflow",
            "主力净流入-净占比": "main_net_ratio",
            "超大单净流入-净额": "super_large_net_inflow",
            "大单净流入-净额": "large_net_inflow",
            "中单净流入-净额": "medium_net_inflow",
            "小单净流入-净额": "small_net_inflow",
        }
    )
    renamed["trade_date"] = pd.to_datetime(renamed["trade_date"]).dt.date

    return renamed[
        [
            "trade_date",
            "main_net_inflow",
            "main_net_ratio",
            "super_large_net_inflow",
            "large_net_inflow",
            "medium_net_inflow",
            "small_net_inflow",
        ]
    ]
