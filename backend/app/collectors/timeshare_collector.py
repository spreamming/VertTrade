from datetime import date, datetime

import pandas as pd
import requests

from ..utils.network import without_system_proxy


def _market_symbol(code: str) -> str:
    prefix = "sh" if code.startswith("6") else "sz"
    return f"{prefix}{code}"


def _secid_for_code(code: str) -> str:
    market = "1" if code.startswith("6") else "0"
    return f"{market}.{code}"


def fetch_timeshare(code: str) -> tuple[pd.DataFrame, str]:
    try:
        frame = _fetch_timeshare_tencent(code)
        if not frame.empty:
            return frame, "tencent"
    except (requests.RequestException, ValueError):
        pass

    frame = _fetch_timeshare_eastmoney(code)
    if frame.empty:
        raise ValueError(f"暂无 {code} 的分时图数据")

    return frame, "eastmoney"


def _fetch_timeshare_tencent(code: str) -> pd.DataFrame:
    symbol = _market_symbol(code)
    with without_system_proxy():
        response = requests.get(
            "https://web.ifzq.gtimg.cn/appstock/app/minute/query",
            params={"code": symbol},
            timeout=8,
        )
    response.raise_for_status()
    payload = response.json().get("data", {}).get(symbol, {}).get("data", {})
    rows = payload.get("data", []) or []
    if not rows:
        return pd.DataFrame()

    parsed_rows = []
    cumulative_amount = 0.0
    cumulative_volume = 0.0
    today = date.today()
    for raw in rows:
        parts = raw.split()
        if len(parts) < 4:
            continue
        hhmm, price, volume, amount = parts[:4]
        timestamp = datetime.combine(
            today,
            datetime.strptime(hhmm, "%H%M").time(),
        )
        price_value = float(price)
        volume_value = float(volume)
        amount_value = float(amount)
        cumulative_amount += amount_value
        cumulative_volume += volume_value
        average_price = (
            cumulative_amount / cumulative_volume / 100
            if cumulative_volume > 0
            else None
        )
        parsed_rows.append(
            {
                "time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "price": price_value,
                "average_price": average_price,
                "volume": volume_value,
                "amount": amount_value,
            }
        )

    return pd.DataFrame(parsed_rows)


def _fetch_timeshare_eastmoney(code: str) -> pd.DataFrame:
    params = {
        "secid": _secid_for_code(code),
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "iscr": "0",
        "ndays": "1",
    }
    with without_system_proxy():
        response = requests.get(
            "https://push2.eastmoney.com/api/qt/stock/trends2/get",
            params=params,
            timeout=10,
        )
    response.raise_for_status()
    trends = response.json().get("data", {}).get("trends", []) or []
    if not trends:
        return pd.DataFrame()

    parsed_rows = []
    for row in trends:
        parts = row.split(",")
        if len(parts) < 8:
            continue
        parsed_rows.append(
            {
                "time": parts[0],
                "price": float(parts[2]),
                "average_price": float(parts[7]),
                "volume": float(parts[5]),
                "amount": float(parts[6]),
            }
        )

    return pd.DataFrame(parsed_rows)
