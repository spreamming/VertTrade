from datetime import date, datetime

import pandas as pd
import requests

from ..utils.network import without_system_proxy


def _market_symbol(code: str) -> str:
    prefix = "sh" if code.startswith("6") else "sz"
    return f"{prefix}{code}"


def fetch_timeshare(code: str) -> pd.DataFrame:
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
