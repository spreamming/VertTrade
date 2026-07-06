import pandas as pd
import requests
from io import StringIO
from akshare.stock_feature import stock_technology_ths as ths

from .sector_collector import fetch_industry_sectors
from ..utils.network import without_system_proxy
from ..utils.provider_locks import THS_PROVIDER_LOCK


class RankingDataSourceError(RuntimeError):
    pass


def _validate_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        missing = "、".join(sorted(missing_columns))
        raise RankingDataSourceError(f"{label}数据源缺少字段：{missing}")


def _exchange_for_code(code: str) -> str:
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    if code.startswith(("8", "4", "9")):
        return "BJ"
    return "UNKNOWN"


def _parse_chinese_amount(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "--"}:
        return None
    if text.endswith("%"):
        text = text[:-1]
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


def fetch_stock_spot_rankings() -> pd.DataFrame:
    return fetch_stock_spot_rankings_ths()

def _ths_headers() -> dict:
    with THS_PROVIDER_LOCK:
        js_code = ths.py_mini_racer.MiniRacer()
        js_code.eval(ths._get_file_content_ths("ths.js"))
        v_code = js_code.call("v")
    return {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"v={v_code}",
    }


def _fetch_ths_stock_page(field: str, order: str, headers: dict | None = None) -> pd.DataFrame:
    url = (
        "http://q.10jqka.com.cn/index/index/board/all/"
        f"field/{field}/order/{order}/page/1/ajax/1/"
    )
    with without_system_proxy():
        response = requests.get(url, headers=headers or _ths_headers(), timeout=4)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables:
        return pd.DataFrame()
    return tables[0]


def fetch_stock_spot_rankings_ths() -> pd.DataFrame:
    frames = []
    headers = _ths_headers()
    # Some THS sort pages (notably asc and turnover) frequently return 403.
    # Keep the request fast and stable with the pages that are currently usable.
    for field, order in (("zdf", "desc"), ("cje", "desc")):
        try:
            frames.append(_fetch_ths_stock_page(field, order, headers=headers))
        except (requests.RequestException, ValueError):
            continue

    if not frames:
        return fetch_stock_spot_rankings_ths_fund_flow()

    raw = pd.concat(frames, ignore_index=True)
    required = {"代码", "名称", "现价", "涨跌幅(%)", "成交额", "换手(%)"}
    _validate_columns(raw, required, "同花顺 A 股行情排行")
    renamed = raw.rename(
        columns={
            "代码": "code",
            "名称": "name",
            "现价": "latest_price",
            "涨跌幅(%)": "change_percent",
            "成交额": "amount",
            "换手(%)": "turnover_rate",
        }
    )
    renamed["code"] = renamed["code"].astype(str).str.zfill(6)
    renamed["exchange"] = renamed["code"].map(_exchange_for_code)
    renamed["amount"] = renamed["amount"].map(_parse_chinese_amount)
    renamed = renamed.drop_duplicates(subset=["code"], keep="first")
    result = renamed[
        [
            "code",
            "name",
            "exchange",
            "latest_price",
            "change_percent",
            "amount",
            "turnover_rate",
        ]
    ]
    result.attrs["source"] = "akshare_ths"
    return result


def fetch_stock_spot_rankings_ths_fund_flow() -> pd.DataFrame:
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
        raise RankingDataSourceError("同花顺资金流即时榜无表格数据")

    raw = tables[0]
    required = {"股票代码", "股票简称", "最新价", "涨跌幅", "换手率", "成交额(元)"}
    _validate_columns(raw, required, "同花顺资金流即时榜")
    frame = raw.rename(
        columns={
            "股票代码": "code",
            "股票简称": "name",
            "最新价": "latest_price",
            "涨跌幅": "change_percent",
            "换手率": "turnover_rate",
            "成交额(元)": "amount",
        }
    )
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    frame["exchange"] = frame["code"].map(_exchange_for_code)
    frame["change_percent"] = frame["change_percent"].map(_parse_chinese_amount)
    frame["turnover_rate"] = frame["turnover_rate"].map(_parse_chinese_amount)
    frame["amount"] = frame["amount"].map(_parse_chinese_amount)
    result = frame[
        [
            "code",
            "name",
            "exchange",
            "latest_price",
            "change_percent",
            "amount",
            "turnover_rate",
        ]
    ]
    result.attrs["source"] = "akshare_ths_fund_flow"
    return result


def fetch_stock_moneyflow_rankings() -> pd.DataFrame:
    return fetch_stock_moneyflow_rankings_ths()


def fetch_stock_moneyflow_rankings_ths() -> pd.DataFrame:
    url = "http://data.10jqka.com.cn/funds/ggzjl/field/zdf/order/desc/page/1/ajax/1/free/1/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
    }
    with without_system_proxy():
        response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables:
        raise RankingDataSourceError("同花顺个股资金流无表格数据")

    raw = tables[0]
    required = {"股票代码", "股票简称", "涨跌幅", "净额(元)"}
    _validate_columns(raw, required, "同花顺个股资金流排行")
    frame = raw.rename(
        columns={
            "股票代码": "code",
            "股票简称": "name",
            "涨跌幅": "change_percent",
            "净额(元)": "main_net_inflow",
        }
    )
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    frame["exchange"] = frame["code"].map(_exchange_for_code)
    frame["change_percent"] = frame["change_percent"].map(_parse_chinese_amount)
    frame["main_net_inflow"] = frame["main_net_inflow"].map(_parse_chinese_amount)
    frame.attrs["source"] = "akshare_ths"
    return frame[
        [
            "code",
            "name",
            "exchange",
            "change_percent",
            "main_net_inflow",
        ]
    ]

def fetch_sector_rankings() -> pd.DataFrame:
    return fetch_industry_sectors()
