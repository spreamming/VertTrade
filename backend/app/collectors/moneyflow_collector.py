import akshare as ak
import pandas as pd
import requests
from datetime import date
from io import StringIO

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


def _secid_for_stock(code: str, exchange: str | None = None) -> str:
    market = "1" if market_code_for_stock(code, exchange) == "sh" else "0"
    return f"{market}.{code}"


def _fetch_stock_moneyflow_eastmoney_direct(
    code: str,
    exchange: str | None = None,
) -> pd.DataFrame:
    params = {
        "lmt": "0",
        "klt": "101",
        "secid": _secid_for_stock(code, exchange),
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
    }
    with without_system_proxy():
        response = requests.get(
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
            params=params,
            timeout=10,
        )
    response.raise_for_status()
    klines = response.json().get("data", {}).get("klines", []) or []
    if not klines:
        return pd.DataFrame()

    frame = pd.DataFrame([row.split(",") for row in klines])
    frame = frame.iloc[:, :11]
    frame.columns = [
        "trade_date",
        "main_net_inflow",
        "small_net_inflow",
        "medium_net_inflow",
        "large_net_inflow",
        "super_large_net_inflow",
        "main_net_ratio",
        "small_net_ratio",
        "medium_net_ratio",
        "large_net_ratio",
        "super_large_net_ratio",
    ]
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    for column in [
        "main_net_inflow",
        "main_net_ratio",
        "super_large_net_inflow",
        "large_net_inflow",
        "medium_net_inflow",
        "small_net_inflow",
    ]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame[
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


def _parse_chinese_amount(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "--"}:
        return None
    multiplier = 1.0
    if text.endswith("亿"):
        multiplier = 100_000_000.0
        text = text[:-1]
    elif text.endswith("万"):
        multiplier = 10_000.0
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def _fetch_stock_moneyflow_ths_snapshot(code: str) -> pd.DataFrame:
    url = "http://data.10jqka.com.cn/funds/ggzjl/field/zdf/order/desc/page/1/ajax/1/free/1/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
    }
    with without_system_proxy():
        response = requests.get(url, headers=headers, timeout=8)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables:
        return pd.DataFrame()

    raw = tables[0]
    if not {"股票代码", "净额(元)"}.issubset(raw.columns):
        return pd.DataFrame()

    raw["股票代码"] = raw["股票代码"].astype(str).str.zfill(6)
    matched = raw[raw["股票代码"] == code]
    if matched.empty:
        return pd.DataFrame()

    row = matched.iloc[0]
    return pd.DataFrame(
        [
            {
                "trade_date": date.today(),
                "main_net_inflow": _parse_chinese_amount(row.get("净额(元)")),
                "main_net_ratio": None,
                "super_large_net_inflow": None,
                "large_net_inflow": None,
                "medium_net_inflow": None,
                "small_net_inflow": None,
            }
        ]
    )


def fetch_stock_moneyflow(code: str, exchange: str | None = None) -> pd.DataFrame:
    market = market_code_for_stock(code, exchange)
    try:
        with without_system_proxy():
            frame = ak.stock_individual_fund_flow(stock=code, market=market)
    except (requests.RequestException, ValueError):
        try:
            return _fetch_stock_moneyflow_eastmoney_direct(code, exchange)
        except (requests.RequestException, ValueError):
            return _fetch_stock_moneyflow_ths_snapshot(code)

    if frame.empty:
        try:
            return _fetch_stock_moneyflow_eastmoney_direct(code, exchange)
        except (requests.RequestException, ValueError):
            return _fetch_stock_moneyflow_ths_snapshot(code)

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
