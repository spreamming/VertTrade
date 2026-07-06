from datetime import datetime

import requests

from ..utils.network import without_system_proxy


class RealtimeQuoteDataSourceError(RuntimeError):
    pass


EASTMONEY_QUOTE_HOSTS = (
    "https://push2.eastmoney.com",
    "https://82.push2.eastmoney.com",
    "https://81.push2.eastmoney.com",
)


def _secid_for_code(code: str) -> str:
    market = "1" if code.startswith("6") else "0"
    return f"{market}.{code}"


def _market_prefix_for_code(code: str) -> str:
    return "sh" if code.startswith("6") else "sz"


def _scaled(value: float | int | None) -> float | None:
    if value is None or value == "-":
        return None
    return float(value) / 100


def _float_or_none(value: str | float | int | None) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    return float(value)


def _fetch_tencent_live_quote(code: str) -> dict:
    symbol = f"{_market_prefix_for_code(code)}{code}"
    with without_system_proxy():
        response = requests.get(
            "https://qt.gtimg.cn/q=" + symbol,
            timeout=6,
        )
    response.raise_for_status()
    text = response.text
    if '="' not in text:
        raise RealtimeQuoteDataSourceError("腾讯实时行情响应格式异常")
    payload = text.split('="', 1)[1].rstrip('";\n')
    fields = payload.split("~")
    if len(fields) < 39:
        raise RealtimeQuoteDataSourceError("腾讯实时行情字段不足")

    quote_time = None
    if fields[30]:
        quote_time = datetime.strptime(fields[30], "%Y%m%d%H%M%S")

    return {
        "code": fields[2].zfill(6),
        "name": fields[1] or code,
        "latest_price": _float_or_none(fields[3]),
        "change_amount": _float_or_none(fields[31]),
        "change_percent": _float_or_none(fields[32]),
        "open": _float_or_none(fields[5]),
        "high": _float_or_none(fields[33]),
        "low": _float_or_none(fields[34]),
        "pre_close": _float_or_none(fields[4]),
        "volume": _float_or_none(fields[36]),
        "amount": (_float_or_none(fields[37]) or 0) * 10_000,
        "turnover_rate": _float_or_none(fields[38]),
        "trade_date": (quote_time or datetime.now()).date(),
        "quote_time": quote_time,
        "source": "tencent_live",
    }


def fetch_live_quote(code: str) -> dict:
    try:
        return _fetch_tencent_live_quote(code)
    except (requests.RequestException, ValueError, RealtimeQuoteDataSourceError):
        pass

    params = {
        "secid": _secid_for_code(code),
        "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f86,f168,f169,f170",
    }
    last_error: Exception | None = None

    for host in EASTMONEY_QUOTE_HOSTS:
        try:
            with without_system_proxy():
                response = requests.get(
                    f"{host}/api/qt/stock/get",
                    params=params,
                    timeout=6,
                )
            response.raise_for_status()
            data = response.json().get("data")
            if not data:
                continue
            latest_price = _scaled(data.get("f43"))
            pre_close = _scaled(data.get("f60"))
            change_amount = _scaled(data.get("f169"))
            change_percent = _scaled(data.get("f170"))
            quote_time = (
                datetime.fromtimestamp(data.get("f86"))
                if data.get("f86")
                else None
            )
            return {
                "code": str(data.get("f57") or code).zfill(6),
                "name": data.get("f58") or code,
                "latest_price": latest_price,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "open": _scaled(data.get("f46")),
                "high": _scaled(data.get("f44")),
                "low": _scaled(data.get("f45")),
                "pre_close": pre_close,
                "volume": data.get("f47"),
                "amount": data.get("f48"),
                "turnover_rate": _scaled(data.get("f168")),
                "trade_date": (quote_time or datetime.now()).date(),
                "quote_time": quote_time,
                "source": "eastmoney_live",
            }
        except (requests.RequestException, ValueError) as exc:
            last_error = exc

    raise RealtimeQuoteDataSourceError(f"实时行情数据源暂不可用：{last_error}")
