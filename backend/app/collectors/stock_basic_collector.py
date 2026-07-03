import akshare as ak
import pandas as pd

from ..utils import infer_exchange
from ..utils.network import without_system_proxy


def fetch_stock_list() -> pd.DataFrame:
    with without_system_proxy():
        frame = ak.stock_info_a_code_name()
    frame = frame.rename(columns={"code": "code", "name": "name"})
    frame["exchange"] = frame["code"].astype(str).map(infer_exchange)
    return frame[["code", "name", "exchange"]]
