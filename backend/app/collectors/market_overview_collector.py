from datetime import datetime

import akshare as ak
import requests

from ..utils.network import without_system_proxy


class MarketOverviewDataSourceError(RuntimeError):
    pass


MAJOR_INDICES = (
    {"code": "000001", "symbol": "sh000001", "name": "上证指数", "exchange": "SH"},
    {"code": "399001", "symbol": "sz399001", "name": "深证成指", "exchange": "SZ"},
    {"code": "399006", "symbol": "sz399006", "name": "创业板指", "exchange": "SZ"},
    {"code": "000688", "symbol": "sh000688", "name": "科创50", "exchange": "SH"},
)


def _float_or_none(value: str | float | int | None) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    return float(value)


def _parse_tencent_index_line(line: str) -> dict | None:
    if '="' not in line:
        return None

    symbol = line.split("=")[0].split("_")[-1]
    payload = line.split('="', 1)[1].rstrip('";\n')
    fields = payload.split("~")
    if len(fields) < 39:
        return None

    meta = next((item for item in MAJOR_INDICES if item["symbol"] == symbol), None)
    if meta is None:
        return None

    quote_time = None
    if fields[30]:
        quote_time = datetime.strptime(fields[30], "%Y%m%d%H%M%S")

    amount = _float_or_none(fields[37])
    if amount is not None:
        amount *= 10_000

    return {
        "code": meta["code"],
        "name": fields[1] or meta["name"],
        "exchange": meta["exchange"],
        "latest_price": _float_or_none(fields[3]),
        "change_amount": _float_or_none(fields[31]),
        "change_percent": _float_or_none(fields[32]),
        "volume": _float_or_none(fields[36]),
        "amount": amount,
        "quote_time": quote_time,
        "source": "tencent",
    }


def fetch_major_indices() -> list[dict]:
    symbols = ",".join(item["symbol"] for item in MAJOR_INDICES)
    with without_system_proxy():
        response = requests.get(
            "https://qt.gtimg.cn/q=" + symbols,
            timeout=8,
        )
    response.raise_for_status()

    indices: list[dict] = []
    for line in response.text.strip().split(";"):
        parsed = _parse_tencent_index_line(line.strip())
        if parsed and parsed["latest_price"] is not None:
            indices.append(parsed)

    if not indices:
        raise MarketOverviewDataSourceError("暂时无法获取主要指数行情")

    return indices


def fetch_market_breadth() -> dict:
    with without_system_proxy():
        frame = ak.stock_market_activity_legu()

    lookup = {
        str(row["item"]).strip(): row["value"]
        for row in frame.to_dict(orient="records")
    }

    as_of_raw = lookup.get("统计日期")
    as_of = None
    if as_of_raw:
        as_of = datetime.strptime(str(as_of_raw), "%Y-%m-%d %H:%M:%S")

    activity_ratio = lookup.get("活跃度")
    if activity_ratio is not None:
        activity_ratio = float(str(activity_ratio).replace("%", ""))

    return {
        "rising_count": _int_or_none(lookup.get("上涨")),
        "falling_count": _int_or_none(lookup.get("下跌")),
        "flat_count": _int_or_none(lookup.get("平盘")),
        "limit_up_count": _int_or_none(lookup.get("涨停")),
        "limit_down_count": _int_or_none(lookup.get("跌停")),
        "suspended_count": _int_or_none(lookup.get("停牌")),
        "activity_ratio": activity_ratio,
        "as_of": as_of,
        "source": "legu",
    }


def _int_or_none(value) -> int | None:
    if value in (None, "", "-", "--"):
        return None
    return int(float(value))
