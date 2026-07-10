import pandas as pd
import requests

from ..utils.network import without_system_proxy
from .sector_collector import SectorDataSourceError, _resolve_eastmoney_board_code


def fetch_sector_moneyflow(name: str, limit: int = 120) -> pd.DataFrame:
    board_code = _resolve_eastmoney_board_code(name)
    if not board_code:
        raise SectorDataSourceError(f"未找到板块 {name} 的东方财富代码")

    params = {
        "secid": f"90.{board_code}",
        "lmt": str(limit),
        "klt": "101",
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
    rows = response.json().get("data", {}).get("klines", []) or []
    if not rows:
        raise SectorDataSourceError(f"暂无 {name} 的板块资金流数据")

    parsed_rows = []
    for row in rows:
        parts = row.split(",")
        if len(parts) < 2:
            continue
        main_net = float(parts[1])
        parsed_rows.append(
            {
                "trade_date": parts[0],
                "main_net_inflow": main_net,
                "main_net_ratio": float(parts[6]) if len(parts) > 6 and parts[6] else None,
            }
        )

    frame = pd.DataFrame(parsed_rows)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    return frame
