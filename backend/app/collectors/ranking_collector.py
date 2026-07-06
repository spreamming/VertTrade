import akshare as ak
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from akshare.stock_feature import stock_technology_ths as ths

from .sector_collector import fetch_industry_sectors
from ..utils.network import without_system_proxy


class RankingDataSourceError(RuntimeError):
    pass


STOCK_SPOT_COLUMNS = {
    "代码",
    "名称",
    "最新价",
    "涨跌幅",
    "成交额",
    "换手率",
}

STOCK_MONEYFLOW_COLUMNS = {
    "股票代码",
    "股票简称",
    "涨跌幅",
    "主力净流入-净额",
}

EASTMONEY_HOSTS = (
    "https://82.push2.eastmoney.com",
    "https://81.push2.eastmoney.com",
    "https://push2.eastmoney.com",
)


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


def _request_eastmoney(params: dict) -> list[dict]:
    last_error: Exception | None = None
    for host in EASTMONEY_HOSTS:
        try:
            with without_system_proxy():
                response = requests.get(
                    f"{host}/api/qt/clist/get",
                    params=params,
                    timeout=3,
                )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", {}).get("diff", []) or []
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
    raise RankingDataSourceError(
        f"东方财富排行数据源暂不可用：{last_error}"
    )


def _normalize_stock_rows(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "code": row.get("f12"),
                "name": row.get("f14"),
                "latest_price": row.get("f2"),
                "change_percent": row.get("f3"),
                "amount": row.get("f6"),
                "turnover_rate": row.get("f8"),
            }
            for row in rows
        ]
    )
    if frame.empty:
        frame.attrs["source"] = "akshare_em_direct"
        return frame
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    frame["exchange"] = frame["code"].map(_exchange_for_code)
    frame.attrs["source"] = "akshare_em_direct"
    return frame[
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


def _stock_rank_params(fid: str, po: str, limit: int) -> dict:
    return {
        "pn": "1",
        "pz": str(limit),
        "po": po,
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fid": fid,
        "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
        "fields": "f2,f3,f6,f8,f12,f14",
    }


def fetch_stock_spot_rankings() -> pd.DataFrame:
    frames = []
    rank_specs = (("f3", "1"), ("f3", "0"), ("f6", "1"), ("f8", "1"))
    executor = ThreadPoolExecutor(max_workers=4)
    try:
        futures = [
            executor.submit(
                _request_eastmoney,
                _stock_rank_params(fid=fid, po=po, limit=80),
            )
            for fid, po in rank_specs
        ]
        for future in futures:
            try:
                rows = future.result(timeout=5)
            except Exception:
                continue
            frames.append(_normalize_stock_rows(rows))
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    if frames:
        frame = pd.concat(frames, ignore_index=True)
        frame = frame.drop_duplicates(subset=["code"], keep="first")
        frame.attrs["source"] = "akshare_em_direct"
        return frame

    return fetch_stock_spot_rankings_ths()


def _ths_headers() -> dict:
    js_code = ths.py_mini_racer.MiniRacer()
    js_code.eval(ths._get_file_content_ths("ths.js"))
    v_code = js_code.call("v")
    return {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"v={v_code}",
    }


def _fetch_ths_stock_page(field: str, order: str) -> pd.DataFrame:
    url = (
        "http://q.10jqka.com.cn/index/index/board/all/"
        f"field/{field}/order/{order}/page/1/ajax/1/"
    )
    with without_system_proxy():
        response = requests.get(url, headers=_ths_headers(), timeout=10)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables:
        return pd.DataFrame()
    return tables[0]


def fetch_stock_spot_rankings_ths() -> pd.DataFrame:
    frames = []
    for field, order in (("zdf", "desc"), ("zdf", "asc"), ("cje", "desc"), ("hsl", "desc")):
        try:
            frames.append(_fetch_ths_stock_page(field, order))
        except (requests.RequestException, ValueError):
            continue

    if not frames:
        raise RankingDataSourceError("同花顺行情排行数据源暂不可用")

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


def fetch_stock_moneyflow_rankings() -> pd.DataFrame:
    try:
        rows = []
        for po in ("1", "0"):
            rows.extend(_request_eastmoney(_moneyflow_rank_params(po=po, limit=80)))
        frame = _normalize_moneyflow_rows(rows)
        if not frame.empty:
            return frame
    except RankingDataSourceError:
        pass

    return fetch_stock_moneyflow_rankings_ths()


def _moneyflow_rank_params(po: str, limit: int) -> dict:
    return {
        "pn": "1",
        "pz": str(limit),
        "po": po,
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "ut": "b2884a393a59ad64002292a3e90d46a5",
        "fid": "f62",
        "fs": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2",
        "fields": "f12,f14,f2,f3,f62,f184",
    }


def _normalize_moneyflow_rows(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "code": row.get("f12"),
                "name": row.get("f14"),
                "change_percent": row.get("f3"),
                "main_net_inflow": row.get("f62"),
            }
            for row in rows
        ]
    )
    if frame.empty:
        frame.attrs["source"] = "akshare_em_direct"
        return frame
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    frame["exchange"] = frame["code"].map(_exchange_for_code)
    frame = frame.drop_duplicates(subset=["code"], keep="first")
    frame.attrs["source"] = "akshare_em_direct"
    return frame[
        [
            "code",
            "name",
            "exchange",
            "change_percent",
            "main_net_inflow",
        ]
    ]


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


def fetch_stock_moneyflow_rankings_akshare() -> pd.DataFrame:
    with without_system_proxy():
        frame = ak.stock_individual_fund_flow_rank(indicator="今日")

    if frame.empty:
        frame.attrs["source"] = "akshare_em"
        return frame

    _validate_columns(frame, STOCK_MONEYFLOW_COLUMNS, "个股资金流排行")
    renamed = frame.rename(
        columns={
            "股票代码": "code",
            "股票简称": "name",
            "涨跌幅": "change_percent",
            "主力净流入-净额": "main_net_inflow",
        }
    )
    renamed["exchange"] = renamed["code"].map(_exchange_for_code)
    result = renamed[
        [
            "code",
            "name",
            "exchange",
            "change_percent",
            "main_net_inflow",
        ]
    ]
    result.attrs["source"] = "akshare_em"
    return result


def fetch_sector_rankings() -> pd.DataFrame:
    return fetch_industry_sectors()
