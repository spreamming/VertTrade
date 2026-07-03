import akshare as ak
import pandas as pd
import requests
from io import StringIO

from ..utils.network import without_system_proxy


class SectorDataSourceError(RuntimeError):
    pass


SECTOR_COLUMNS = {
    "板块代码",
    "板块名称",
    "最新价",
    "涨跌额",
    "涨跌幅",
    "总市值",
    "换手率",
    "上涨家数",
    "下跌家数",
    "领涨股票",
    "领涨股票-涨跌幅",
}

CONSTITUENT_COLUMNS = {
    "代码",
    "名称",
    "最新价",
    "涨跌幅",
    "涨跌额",
    "成交量",
    "成交额",
    "换手率",
    "市盈率-动态",
    "市净率",
}

THS_CONSTITUENT_COLUMNS = {
    "代码",
    "名称",
    "现价",
    "涨跌幅(%)",
    "涨跌",
    "换手(%)",
    "成交额",
    "市盈率",
}

THS_SUMMARY_COLUMNS = {
    "板块",
    "涨跌幅",
    "总成交额",
    "净流入",
    "上涨家数",
    "下跌家数",
    "领涨股",
    "领涨股-涨跌幅",
}


def _validate_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        missing = "、".join(sorted(missing_columns))
        raise SectorDataSourceError(f"{label}数据源缺少字段：{missing}")


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
    text = str(value).strip()
    if text in {"", "--", "-"}:
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


def fetch_industry_sectors() -> pd.DataFrame:
    try:
        with without_system_proxy():
            frame = ak.stock_board_industry_name_em()
    except requests.RequestException:
        return fetch_industry_sectors_ths()

    if frame.empty:
        frame.attrs["source"] = "akshare_em"
        return frame

    _validate_columns(frame, SECTOR_COLUMNS, "行业板块")
    renamed = frame.rename(
        columns={
            "板块代码": "code",
            "板块名称": "name",
            "最新价": "latest_price",
            "涨跌额": "change_amount",
            "涨跌幅": "change_percent",
            "总市值": "market_value",
            "换手率": "turnover_rate",
            "上涨家数": "rising_count",
            "下跌家数": "falling_count",
            "领涨股票": "leading_stock",
            "领涨股票-涨跌幅": "leading_stock_change_percent",
        }
    )
    renamed["amount"] = None
    renamed["main_net_inflow"] = None

    result = renamed[
        [
            "code",
            "name",
            "latest_price",
            "change_amount",
            "change_percent",
            "amount",
            "main_net_inflow",
            "market_value",
            "turnover_rate",
            "rising_count",
            "falling_count",
            "leading_stock",
            "leading_stock_change_percent",
        ]
    ]
    result.attrs["source"] = "akshare_em"
    return result


def fetch_industry_sectors_ths() -> pd.DataFrame:
    with without_system_proxy():
        summary = ak.stock_board_industry_summary_ths()
        names = ak.stock_board_industry_name_ths()

    if summary.empty:
        summary.attrs["source"] = "akshare_ths"
        return summary

    _validate_columns(summary, THS_SUMMARY_COLUMNS, "同花顺行业板块")
    if {"name", "code"}.difference(names.columns):
        raise SectorDataSourceError("同花顺行业板块数据源缺少字段：name、code")

    code_by_name = dict(zip(names["name"], names["code"], strict=False))
    renamed = summary.rename(
        columns={
            "板块": "name",
            "涨跌幅": "change_percent",
            "总成交额": "amount",
            "净流入": "main_net_inflow",
            "上涨家数": "rising_count",
            "下跌家数": "falling_count",
            "领涨股": "leading_stock",
            "领涨股-涨跌幅": "leading_stock_change_percent",
        }
    )
    renamed["code"] = renamed["name"].map(code_by_name)
    renamed["latest_price"] = None
    renamed["change_amount"] = None
    renamed["market_value"] = None
    renamed["turnover_rate"] = None
    renamed["amount"] = renamed["amount"] * 100_000_000
    renamed["main_net_inflow"] = renamed["main_net_inflow"] * 100_000_000

    result = renamed[
        [
            "code",
            "name",
            "latest_price",
            "change_amount",
            "change_percent",
            "amount",
            "main_net_inflow",
            "market_value",
            "turnover_rate",
            "rising_count",
            "falling_count",
            "leading_stock",
            "leading_stock_change_percent",
        ]
    ]
    result.attrs["source"] = "akshare_ths"
    return result


def fetch_industry_constituents(symbol: str) -> pd.DataFrame:
    try:
        with without_system_proxy():
            frame = ak.stock_board_industry_cons_em(symbol=symbol)
    except (requests.RequestException, ValueError, IndexError):
        return fetch_industry_constituents_ths(symbol)

    if frame.empty:
        return fetch_industry_constituents_ths(symbol)

    _validate_columns(frame, CONSTITUENT_COLUMNS, "板块成分股")
    renamed = frame.rename(
        columns={
            "代码": "code",
            "名称": "name",
            "最新价": "latest_price",
            "涨跌额": "change_amount",
            "涨跌幅": "change_percent",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turnover_rate",
            "市盈率-动态": "pe_dynamic",
            "市净率": "pb",
        }
    )
    renamed["exchange"] = renamed["code"].map(_exchange_for_code)

    result = renamed[
        [
            "code",
            "name",
            "exchange",
            "latest_price",
            "change_amount",
            "change_percent",
            "volume",
            "amount",
            "turnover_rate",
            "pe_dynamic",
            "pb",
        ]
    ]
    result.attrs["source"] = "akshare_em"
    return result


def fetch_industry_constituents_ths(symbol: str) -> pd.DataFrame:
    with without_system_proxy():
        names = ak.stock_board_industry_name_ths()

    if {"name", "code"}.difference(names.columns):
        raise SectorDataSourceError("同花顺行业板块数据源缺少字段：name、code")

    if symbol.startswith("88"):
        ths_code = symbol
    else:
        matches = names[names["name"] == symbol]
        if matches.empty:
            raise SectorDataSourceError(f"未找到同花顺行业板块：{symbol}")
        ths_code = str(matches.iloc[0]["code"])

    url = f"http://q.10jqka.com.cn/thshy/detail/code/{ths_code}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    with without_system_proxy():
        response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    if not tables:
        frame = pd.DataFrame()
        frame.attrs["source"] = "akshare_ths"
        return frame

    frame = tables[0]
    _validate_columns(frame, THS_CONSTITUENT_COLUMNS, "同花顺板块成分股")
    renamed = frame.rename(
        columns={
            "代码": "code",
            "名称": "name",
            "现价": "latest_price",
            "涨跌": "change_amount",
            "涨跌幅(%)": "change_percent",
            "换手(%)": "turnover_rate",
            "成交额": "amount",
            "市盈率": "pe_dynamic",
        }
    )
    renamed["code"] = renamed["code"].astype(str).str.zfill(6)
    renamed["exchange"] = renamed["code"].map(_exchange_for_code)
    renamed["amount"] = renamed["amount"].map(_parse_chinese_amount)
    renamed["volume"] = None
    renamed["pb"] = None

    result = renamed[
        [
            "code",
            "name",
            "exchange",
            "latest_price",
            "change_amount",
            "change_percent",
            "volume",
            "amount",
            "turnover_rate",
            "pe_dynamic",
            "pb",
        ]
    ]
    result.attrs["source"] = "akshare_ths"
    return result
