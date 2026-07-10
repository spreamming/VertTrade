from datetime import date

import pandas as pd
import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services import ranking_service
from backend.app.services.market_overview_service import MarketOverviewService
from backend.app.services.sector_service import SectorService
from backend.app.services.stock_service import StockService


def _fake_stock_list() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"code": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"code": "000001", "name": "平安银行", "exchange": "SZ"},
        ]
    )


def _fake_kline(code: str, start: date, end: date, adjust: str = "") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": date(2026, 7, 1),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "pre_close": None,
                "volume": 1000.0,
                "amount": 100000.0,
                "turnover_rate": 1.2,
            },
            {
                "trade_date": date(2026, 7, 2),
                "open": 103.0,
                "high": 106.0,
                "low": 102.0,
                "close": 105.0,
                "pre_close": 103.0,
                "volume": 1200.0,
                "amount": 120000.0,
                "turnover_rate": 1.4,
            },
        ]
    )


def _fake_moneyflow(code: str, exchange: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": date(2026, 7, 1),
                "main_net_inflow": 100000000.0,
                "main_net_ratio": 3.5,
                "super_large_net_inflow": 40000000.0,
                "large_net_inflow": 60000000.0,
                "medium_net_inflow": -20000000.0,
                "small_net_inflow": -80000000.0,
            },
            {
                "trade_date": date(2026, 7, 2),
                "main_net_inflow": -50000000.0,
                "main_net_ratio": -2.1,
                "super_large_net_inflow": -20000000.0,
                "large_net_inflow": -30000000.0,
                "medium_net_inflow": 10000000.0,
                "small_net_inflow": 40000000.0,
            },
        ]
    )


def _fake_sectors() -> pd.DataFrame:
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


def _fake_constituents(symbol: str) -> pd.DataFrame:
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
        ]
    )
    frame.attrs["source"] = "akshare_em"
    return frame


@pytest.fixture
def client(monkeypatch):
    StockService._live_quote_cache.clear()
    StockService._intraday_kline_cache.clear()
    StockService._timeshare_cache.clear()
    SectorService.clear_chart_cache()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_list",
        _fake_stock_list,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_daily_kline",
        _fake_kline,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_moneyflow",
        _fake_moneyflow,
    )
    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_industry_sectors",
        _fake_sectors,
    )
    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_industry_constituents",
        _fake_constituents,
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
            ]
        ),
    )
    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_major_indices",
        lambda: [
            {
                "code": "000001",
                "name": "上证指数",
                "exchange": "SH",
                "latest_price": 3000.0,
                "change_amount": 10.0,
                "change_percent": 0.33,
                "source": "tencent",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_market_breadth",
        lambda: {
            "rising_count": 2500,
            "falling_count": 1800,
            "flat_count": 100,
            "limit_up_count": 45,
            "limit_down_count": 12,
            "source": "legu",
        },
    )
    ranking_service.RankingService._cache.clear()
    MarketOverviewService.clear_cache()
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_spot_rankings",
        lambda: pd.DataFrame(
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
            ]
        ),
    )
    monkeypatch.setattr(
        ranking_service,
        "fetch_stock_moneyflow_rankings",
        lambda: pd.DataFrame(
            [
                {
                    "code": "600519",
                    "name": "贵州茅台",
                    "exchange": "SH",
                    "change_percent": -0.71,
                    "main_net_inflow": 100000000.0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        ranking_service,
        "fetch_sector_rankings",
        lambda: _fake_sectors(),
    )

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    SectorService.clear_chart_cache()


def test_get_stock_kline_returns_cached_data_when_provider_fails(
    client: TestClient,
    monkeypatch,
):
    first = client.get("/api/stocks/600519/kline")
    assert first.status_code == 200

    def fail_fetch(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_daily_kline",
        fail_fetch,
    )

    second = client.get("/api/stocks/600519/kline", params={"refresh": "true"})
    assert second.status_code == 200
    assert len(second.json()["bars"]) == 2


def test_get_stock_moneyflow_returns_cached_data_when_provider_fails(
    client: TestClient,
    monkeypatch,
):
    first = client.get("/api/stocks/600519/moneyflow")
    assert first.status_code == 200

    def fail_fetch(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_moneyflow",
        fail_fetch,
    )

    second = client.get("/api/stocks/600519/moneyflow", params={"refresh": "true"})
    assert second.status_code == 200
    assert len(second.json()["bars"]) == 2


@pytest.mark.parametrize("window", [750, 1250])
def test_get_stock_position_supports_extended_windows(client: TestClient, window: int):
    response = client.get("/api/stocks/600519/position", params={"window": window})

    assert response.status_code == 200
    payload = response.json()
    assert payload["window"] == window
    assert payload["position_score"] is not None


def test_sector_kline_uses_cache_within_ttl(client: TestClient, monkeypatch):
    calls = {"count": 0}

    def counting_fetch(name, start_date=None, end_date=None):
        calls["count"] += 1
        return (
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
                ]
            ),
            "akshare_ths",
        )

    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_sector_kline",
        counting_fetch,
    )

    first = client.get(
        "/api/sectors/industries/BK1027/kline",
        params={"name": "小金属"},
    )
    second = client.get(
        "/api/sectors/industries/BK1027/kline",
        params={"name": "小金属"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 1
    assert second.json()["is_stale"] is False


def test_sector_kline_returns_stale_cache_when_provider_fails(
    client: TestClient,
    monkeypatch,
):
    first = client.get(
        "/api/sectors/industries/BK1027/kline",
        params={"name": "小金属"},
    )
    assert first.status_code == 200

    def fail_fetch(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_sector_kline",
        fail_fetch,
    )

    second = client.get(
        "/api/sectors/industries/BK1027/kline",
        params={"name": "小金属", "refresh": "true"},
    )

    assert second.status_code == 200
    assert second.json()["is_stale"] is True
    assert len(second.json()["bars"]) == 1


def test_sector_moneyflow_returns_stale_cache_when_provider_fails(
    client: TestClient,
    monkeypatch,
):
    first = client.get(
        "/api/sectors/industries/BK1027/moneyflow",
        params={"name": "小金属"},
    )
    assert first.status_code == 200

    def fail_fetch(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(
        "backend.app.services.sector_service.fetch_sector_moneyflow",
        fail_fetch,
    )

    second = client.get(
        "/api/sectors/industries/BK1027/moneyflow",
        params={"name": "小金属", "refresh": "true"},
    )

    assert second.status_code == 200
    assert second.json()["is_stale"] is True
    assert len(second.json()["bars"]) == 1


def test_core_review_path_dashboard_sector_stock(client: TestClient):
    client.post("/api/watchlist", json={"code": "600519"})

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert len(dashboard_payload["watchlist_summary"]) == 1
    assert dashboard_payload["market_overview"]["indices"][0]["name"] == "上证指数"

    sector = client.get(
        "/api/sectors/industries/BK1027",
        params={"name": "小金属"},
    )
    assert sector.status_code == 200
    assert sector.json()["constituents"][0]["code"] == "600519"

    stock_kline = client.get("/api/stocks/600519/kline")
    stock_moneyflow = client.get("/api/stocks/600519/moneyflow")
    stock_position = client.get("/api/stocks/600519/position", params={"window": 250})

    assert stock_kline.status_code == 200
    assert stock_moneyflow.status_code == 200
    assert stock_position.status_code == 200

    rankings = client.get("/api/rankings/daily-review")
    assert rankings.status_code == 200
