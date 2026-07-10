from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient
import requests

from backend.app.collectors import sector_collector
from backend.app.collectors.sector_collector import SectorDataSourceError
from backend.app.main import app
from backend.app.services import sector_service


@pytest.fixture
def client(monkeypatch):
    def fake_sectors() -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                {
                    "code": "BK1027",
                    "name": "小金属",
                    "latest_price": 1000.0,
                    "change_amount": 12.3,
                    "change_percent": 1.23,
                    "market_value": 500000000000.0,
                    "turnover_rate": 2.5,
                    "rising_count": 25,
                    "falling_count": 5,
                    "leading_stock": "示例股份",
                    "leading_stock_change_percent": 8.8,
                },
            ]
        )
        frame.attrs["source"] = "akshare_ths"
        return frame

    def fake_constituents(symbol: str) -> pd.DataFrame:
        assert symbol == "小金属"
        frame = pd.DataFrame(
            [
                {
                    "code": "600519",
                    "name": "贵州茅台",
                    "exchange": "SH",
                    "latest_price": 1194.45,
                    "change_amount": -8.55,
                    "change_percent": -0.71,
                    "volume": 1000.0,
                    "amount": 100000.0,
                    "turnover_rate": 1.2,
                    "pe_dynamic": 25.0,
                    "pb": 8.0,
                },
                {
                    "code": "000001",
                    "name": "平安银行",
                    "exchange": "SZ",
                    "latest_price": 12.34,
                    "change_amount": 0.12,
                    "change_percent": 0.98,
                    "volume": 2000.0,
                    "amount": 200000.0,
                    "turnover_rate": 0.8,
                    "pe_dynamic": 6.0,
                    "pb": 0.7,
                },
            ]
        )
        frame.attrs["source"] = "akshare_em"
        return frame

    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_industry_sectors",
        fake_sectors,
    )
    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_industry_constituents",
        fake_constituents,
    )
    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_sector_kline",
        lambda name, start_date=None, end_date=None: (
            pd.DataFrame(
                [
                    {
                        "trade_date": "2026-07-01",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 103.0,
                        "volume": 1000.0,
                        "amount": 100000.0,
                        "turnover_rate": None,
                    },
                    {
                        "trade_date": "2026-07-02",
                        "open": 103.0,
                        "high": 106.0,
                        "low": 102.0,
                        "close": 105.0,
                        "volume": 1200.0,
                        "amount": 120000.0,
                        "turnover_rate": None,
                    },
                ]
            ),
            "akshare_ths",
        ),
    )
    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_sector_moneyflow",
        lambda name, limit=120: pd.DataFrame(
            [
                {
                    "trade_date": date(2026, 7, 1),
                    "main_net_inflow": 100000000.0,
                    "main_net_ratio": 2.5,
                },
                {
                    "trade_date": date(2026, 7, 2),
                    "main_net_inflow": -50000000.0,
                    "main_net_ratio": -1.2,
                },
            ]
        ),
    )

    with TestClient(app) as test_client:
        yield test_client


def test_list_industry_sectors(client: TestClient):
    response = client.get("/api/sectors/industries")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "akshare_ths"
    assert payload["sectors"][0]["code"] == "BK1027"
    assert payload["sectors"][0]["name"] == "小金属"
    assert payload["sectors"][0]["change_percent"] == 1.23


def test_get_industry_sector_constituents(client: TestClient):
    response = client.get(
        "/api/sectors/industries/BK1027",
        params={"name": "小金属"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "BK1027"
    assert payload["name"] == "小金属"
    assert len(payload["constituents"]) == 2
    assert payload["constituents"][0]["code"] == "600519"
    assert payload["constituents"][1]["exchange"] == "SZ"


def test_get_industry_sector_kline(client: TestClient):
    response = client.get(
        "/api/sectors/industries/BK1027/kline",
        params={"name": "小金属"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "小金属"
    assert payload["source"] == "akshare_ths"
    assert len(payload["bars"]) == 2
    assert payload["bars"][1]["close"] == 105.0


def test_get_industry_sector_moneyflow(client: TestClient):
    response = client.get(
        "/api/sectors/industries/BK1027/moneyflow",
        params={"name": "小金属"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "小金属"
    assert payload["source"] == "eastmoney"
    assert payload["bars"][0]["main_net_inflow"] == 100000000.0
    assert payload["bars"][1]["main_net_inflow"] == -50000000.0


def test_sector_collector_validates_required_columns():
    frame = pd.DataFrame([{"板块代码": "BK1027"}])

    with pytest.raises(SectorDataSourceError, match="行业板块数据源缺少字段"):
        sector_collector._validate_columns(
            frame,
            sector_collector.SECTOR_COLUMNS,
            "行业板块",
        )


def test_industry_sector_collector_falls_back_to_ths(monkeypatch):
    def raise_em_error() -> pd.DataFrame:
        raise requests.ConnectionError("eastmoney unavailable")

    def fake_ths_summary() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "板块": "半导体",
                    "涨跌幅": 2.5,
                    "总成交额": 123.0,
                    "净流入": -4.5,
                    "上涨家数": 30,
                    "下跌家数": 8,
                    "领涨股": "示例科技",
                    "领涨股-涨跌幅": 9.9,
                }
            ]
        )

    def fake_ths_names() -> pd.DataFrame:
        return pd.DataFrame([{"name": "半导体", "code": "881121"}])

    monkeypatch.setattr(
        sector_collector.ak,
        "stock_board_industry_name_em",
        raise_em_error,
    )
    monkeypatch.setattr(
        sector_collector.ak,
        "stock_board_industry_summary_ths",
        fake_ths_summary,
    )
    monkeypatch.setattr(
        sector_collector.ak,
        "stock_board_industry_name_ths",
        fake_ths_names,
    )

    frame = sector_collector.fetch_industry_sectors()

    assert frame.iloc[0]["code"] == "881121"
    assert frame.iloc[0]["name"] == "半导体"
    assert frame.iloc[0]["amount"] == 12300000000.0
    assert frame.iloc[0]["main_net_inflow"] == -450000000.0
    assert frame.attrs["source"] == "akshare_ths"


def test_sector_detail_tries_code_when_name_fails(monkeypatch):
    calls: list[str] = []

    def fake_constituents(symbol: str) -> pd.DataFrame:
        calls.append(symbol)
        if symbol == "机器人":
            raise requests.ConnectionError("name failed")
        frame = pd.DataFrame(
            [
                {
                    "code": "920211",
                    "name": "新睿电子",
                    "exchange": "BJ",
                    "latest_price": 158.28,
                    "change_amount": 36.52,
                    "change_percent": 29.99,
                    "volume": 19948,
                    "amount": 294886753.59,
                    "turnover_rate": 34.63,
                    "pe_dynamic": 87.2,
                    "pb": 13.11,
                }
            ]
        )
        frame.attrs["source"] = "akshare_em"
        return frame

    monkeypatch.setattr(
        sector_service,
        "fetch_industry_constituents",
        fake_constituents,
    )

    response = sector_service.SectorService().get_industry_sector(
        code="BK1408",
        name="机器人",
    )

    assert calls == ["机器人", "BK1408"]
    assert response.constituents[0].code == "920211"
    assert response.constituents[0].exchange == "BJ"
    assert response.source == "akshare_em"


def test_industry_constituents_fall_back_to_ths(monkeypatch):
    def raise_em_error(symbol: str) -> pd.DataFrame:
        raise requests.ConnectionError("eastmoney constituents unavailable")

    def fake_ths_names() -> pd.DataFrame:
        return pd.DataFrame([{"name": "贵金属", "code": "881169"}])

    class FakeResponse:
        text = """
        <table>
          <thead>
            <tr>
              <th>序号</th><th>代码</th><th>名称</th><th>现价</th>
              <th>涨跌幅(%)</th><th>涨跌</th><th>涨速(%)</th><th>换手(%)</th>
              <th>量比</th><th>振幅(%)</th><th>成交额</th><th>流通股</th>
              <th>流通市值</th><th>市盈率</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td><td>300139</td><td>晓程科技</td><td>44.05</td>
              <td>12.86</td><td>5.02</td><td>0.0</td><td>30.65</td>
              <td>2.95</td><td>10.71</td><td>30.88亿</td><td>2.34亿</td>
              <td>102.93亿</td><td>67.20</td>
            </tr>
          </tbody>
        </table>
        """

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(
        sector_collector.ak,
        "stock_board_industry_cons_em",
        raise_em_error,
    )
    monkeypatch.setattr(
        sector_collector.ak,
        "stock_board_industry_name_ths",
        fake_ths_names,
    )
    monkeypatch.setattr(
        sector_collector.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    frame = sector_collector.fetch_industry_constituents("贵金属")

    assert frame.attrs["source"] == "akshare_ths"
    assert frame.iloc[0]["code"] == "300139"
    assert frame.iloc[0]["exchange"] == "SZ"
    assert frame.iloc[0]["amount"] == 3088000000.0
