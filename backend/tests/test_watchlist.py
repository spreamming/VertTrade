from datetime import date, datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.market_overview_service import MarketOverviewService


@pytest.fixture
def client(monkeypatch):
    MarketOverviewService.clear_cache()
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

    def fake_stock_list() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"code": "600519", "name": "贵州茅台", "exchange": "SH"},
                {"code": "000001", "name": "平安银行", "exchange": "SZ"},
            ]
        )

    def fake_kline(code: str, start: date, end: date, adjust: str = "") -> pd.DataFrame:
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

    def fake_moneyflow(code: str, exchange: str | None = None) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "trade_date": date(2026, 7, 2),
                    "main_net_inflow": 85000000.0,
                    "main_net_ratio": 4.2,
                    "super_large_net_inflow": 30000000.0,
                    "large_net_inflow": 55000000.0,
                    "medium_net_inflow": None,
                    "small_net_inflow": None,
                },
            ]
        )

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_list",
        fake_stock_list,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_daily_kline",
        fake_kline,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_moneyflow",
        fake_moneyflow,
    )
    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_major_indices",
        lambda: [
            {
                "code": "000001",
                "name": "上证指数",
                "exchange": "SH",
                "latest_price": 3952.49,
                "change_amount": -18.39,
                "change_percent": -0.46,
                "volume": 330849707.0,
                "amount": 790773120000.0,
                "quote_time": datetime(2026, 7, 9, 11, 30),
                "source": "tencent",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_market_breadth",
        lambda: {
            "rising_count": 799,
            "falling_count": 4333,
            "flat_count": 62,
            "limit_up_count": 36,
            "limit_down_count": 20,
            "suspended_count": 9,
            "activity_ratio": 15.36,
            "as_of": datetime(2026, 7, 9, 11, 30),
            "source": "legu",
        },
    )

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    MarketOverviewService.clear_cache()


def test_add_and_list_watchlist_item(client: TestClient):
    response = client.post("/api/watchlist", json={"code": "600519"})

    assert response.status_code == 201
    created = response.json()
    assert created["code"] == "600519"
    assert created["name"] == "贵州茅台"
    assert created["latest_price"] == 105.0

    list_response = client.get("/api/watchlist")

    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["change_amount"] == 2.0
    assert payload[0]["position_score"] == 85.71
    assert payload[0]["position_label"] == "高位观察区"
    assert payload[0]["main_net_inflow"] == 85000000.0
    assert payload[0]["main_net_ratio"] == 4.2


def test_adding_same_stock_is_idempotent(client: TestClient):
    first = client.post("/api/watchlist", json={"code": "600519"}).json()
    second = client.post("/api/watchlist", json={"code": "600519"}).json()

    assert first["id"] == second["id"]
    assert len(client.get("/api/watchlist").json()) == 1


def test_delete_watchlist_item(client: TestClient):
    created = client.post("/api/watchlist", json={"code": "600519"}).json()

    delete_response = client.delete(f"/api/watchlist/{created['id']}")

    assert delete_response.status_code == 204
    assert client.get("/api/watchlist").json() == []


def test_dashboard_returns_watchlist_summary(client: TestClient):
    client.post("/api/watchlist", json={"code": "600519"})

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["watchlist_count"] == 1
    assert payload["watchlist_summary"][0]["code"] == "600519"
    assert payload["watchlist_summary"][0]["position_label"] == "高位观察区"
    assert payload["watchlist_summary"][0]["main_net_inflow"] == 85000000.0
    assert payload["market_overview"]["indices"][0]["name"] == "上证指数"
    assert payload["market_breadth"]["rising_count"] == 799
    assert payload["market_notes"]
