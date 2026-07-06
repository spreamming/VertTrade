import pandas as pd
from fastapi.testclient import TestClient
import pytest
import requests

from backend.app.collectors import ranking_collector
from backend.app.main import app
from backend.app.services import ranking_service


@pytest.fixture(autouse=True)
def clear_ranking_cache():
    ranking_service.RankingService._cache.clear()


def _stock_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "code": "600519",
                "name": "贵州茅台",
                "exchange": "SH",
                "latest_price": 1194.45,
                "change_percent": -0.71,
                "amount": 1000000000.0,
                "turnover_rate": 0.5,
            },
            {
                "code": "000001",
                "name": "平安银行",
                "exchange": "SZ",
                "latest_price": 12.34,
                "change_percent": 2.5,
                "amount": 800000000.0,
                "turnover_rate": 3.0,
            },
        ]
    )
    frame.attrs["source"] = "akshare_em"
    return frame


def _moneyflow_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "code": "600519",
                "name": "贵州茅台",
                "exchange": "SH",
                "change_percent": -0.71,
                "main_net_inflow": -200000000.0,
            },
            {
                "code": "000001",
                "name": "平安银行",
                "exchange": "SZ",
                "change_percent": 2.5,
                "main_net_inflow": 100000000.0,
            },
        ]
    )
    frame.attrs["source"] = "akshare_em"
    return frame


def _sector_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "code": "881169",
                "name": "贵金属",
                "change_percent": 6.17,
                "amount": 40180000000.0,
                "main_net_inflow": -215000000.0,
                "leading_stock": "晓程科技",
            },
            {
                "code": "881121",
                "name": "半导体",
                "change_percent": 1.5,
                "amount": 30000000000.0,
                "main_net_inflow": 740000000.0,
                "leading_stock": "示例科技",
            },
        ]
    )
    frame.attrs["source"] = "akshare_ths"
    return frame


def test_daily_review_returns_ranking_groups(monkeypatch):
    monkeypatch.setattr(ranking_service, "fetch_stock_spot_rankings", _stock_frame)
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_moneyflow_rankings",
        _moneyflow_frame,
    )
    monkeypatch.setattr(ranking_service, "fetch_sector_rankings", _sector_frame)

    with TestClient(app) as client:
        response = client.get(
            "/api/rankings/daily-review",
            params={"limit": 3, "include_stock": "true"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["groups"]) == 8
    gainers = next(group for group in payload["groups"] if group["key"] == "stock_gainers")
    assert gainers["items"][0]["code"] == "000001"
    sector_money = next(
        group for group in payload["groups"] if group["key"] == "sector_moneyflow"
    )
    assert sector_money["source"] == "akshare_ths"
    assert sector_money["items"][0]["name"] == "半导体"
    assert payload["notes"]


def test_daily_review_defaults_to_all_ranking_groups(monkeypatch):
    monkeypatch.setattr(ranking_service, "fetch_stock_spot_rankings", _stock_frame)
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_moneyflow_rankings",
        _moneyflow_frame,
    )
    monkeypatch.setattr(ranking_service, "fetch_sector_rankings", _sector_frame)

    with TestClient(app) as client:
        response = client.get("/api/rankings/daily-review")

    assert response.status_code == 200
    payload = response.json()
    keys = [group["key"] for group in payload["groups"]]
    assert keys == [
        "stock_gainers",
        "stock_losers",
        "stock_amount",
        "stock_turnover",
        "stock_money_inflow",
        "stock_money_outflow",
        "sector_gainers",
        "sector_moneyflow",
    ]
    assert all(group["error"] is None for group in payload["groups"])


def test_daily_review_keeps_other_groups_when_stock_source_fails(monkeypatch):
    def fail_stock_source() -> pd.DataFrame:
        raise requests.ConnectionError("spot unavailable")

    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_spot_rankings",
        fail_stock_source,
    )
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_moneyflow_rankings",
        _moneyflow_frame,
    )
    monkeypatch.setattr(ranking_service, "fetch_sector_rankings", _sector_frame)

    with TestClient(app) as client:
        response = client.get(
            "/api/rankings/daily-review",
            params={"include_stock": "true"},
        )

    assert response.status_code == 200
    payload = response.json()
    stock_gainers = next(
        group for group in payload["groups"] if group["key"] == "stock_gainers"
    )
    assert stock_gainers["items"] == []
    assert stock_gainers["error"] == "暂时无法获取个股涨幅榜，请稍后重试。"
    sector_gainers = next(
        group for group in payload["groups"] if group["key"] == "sector_gainers"
    )
    assert sector_gainers["items"][0]["name"] == "贵金属"


def test_daily_review_uses_short_lived_cache(monkeypatch):
    calls = {"stock": 0, "moneyflow": 0, "sector": 0}

    def stock_frame() -> pd.DataFrame:
        calls["stock"] += 1
        return _stock_frame()

    def moneyflow_frame() -> pd.DataFrame:
        calls["moneyflow"] += 1
        return _moneyflow_frame()

    def sector_frame() -> pd.DataFrame:
        calls["sector"] += 1
        return _sector_frame()

    monkeypatch.setattr(ranking_service, "fetch_stock_spot_rankings", stock_frame)
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_moneyflow_rankings",
        moneyflow_frame,
    )
    monkeypatch.setattr(ranking_service, "fetch_sector_rankings", sector_frame)

    with TestClient(app) as client:
        first = client.get("/api/rankings/daily-review")
        second = client.get("/api/rankings/daily-review")

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls == {"stock": 1, "moneyflow": 1, "sector": 1}
    assert "排行榜缓存" in second.json()["notes"][-1]


def test_stock_spot_rankings_fall_back_to_ths(monkeypatch):
    def fail_eastmoney(params: dict) -> list[dict]:
        raise ranking_collector.RankingDataSourceError("em unavailable")

    def fake_ths_page(field: str, order: str) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "代码": "920510",
                    "名称": "丰光精密",
                    "现价": 32.76,
                    "涨跌幅(%)": 30.0,
                    "成交额": "8.75亿",
                    "换手(%)": 30.78,
                },
                {
                    "代码": "000001",
                    "名称": "平安银行",
                    "现价": 12.34,
                    "涨跌幅(%)": 2.5,
                    "成交额": "8.00亿",
                    "换手(%)": 3.0,
                },
            ]
        )

    monkeypatch.setattr(ranking_collector, "_request_eastmoney", fail_eastmoney)
    monkeypatch.setattr(ranking_collector, "_fetch_ths_stock_page", fake_ths_page)

    frame = ranking_collector.fetch_stock_spot_rankings()

    assert frame.attrs["source"] == "akshare_ths"
    assert frame.iloc[0]["code"] == "920510"
    assert frame.iloc[0]["exchange"] == "BJ"
    assert frame.iloc[0]["amount"] == 875000000.0
