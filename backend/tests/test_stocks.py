from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.collectors.realtime_quote_collector import RealtimeQuoteDataSourceError
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.stock_service import StockService


@pytest.fixture
def client(monkeypatch):
    StockService._live_quote_cache.clear()
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

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_stock_list",
        fake_stock_list,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_daily_kline",
        fake_kline,
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_intraday_kline",
        lambda code, period="1m": pd.DataFrame(
            [
                {
                    "trade_time": "2026-07-06 09:31:00",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.5,
                    "pre_close": None,
                    "volume": 100.0,
                    "amount": 10000.0,
                    "turnover_rate": None,
                },
                {
                    "trade_time": "2026-07-06 09:32:00",
                    "open": 100.5,
                    "high": 102.0,
                    "low": 100.0,
                    "close": 101.5,
                    "pre_close": 100.5,
                    "volume": 120.0,
                    "amount": 12000.0,
                    "turnover_rate": None,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_live_quote",
        lambda code: {
            "code": code,
            "name": "贵州茅台" if code == "600519" else "平安银行",
            "latest_price": 108.0,
            "change_amount": 3.0,
            "change_percent": 2.86,
            "open": 104.0,
            "high": 109.0,
            "low": 103.0,
            "pre_close": 105.0,
            "volume": 1500.0,
            "amount": 150000.0,
            "turnover_rate": 1.8,
            "trade_date": date(2026, 7, 2),
            "quote_time": None,
            "source": "test_live",
        },
    )

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    StockService._live_quote_cache.clear()


def test_search_stocks(client: TestClient):
    response = client.get("/api/stocks/search", params={"keyword": "茅台"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["code"] == "600519"
    assert payload[0]["name"] == "贵州茅台"


def test_get_stock_kline(client: TestClient):
    response = client.get("/api/stocks/600519/kline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "600519"
    assert len(payload["bars"]) == 2
    assert payload["bars"][0]["close"] == 103.0


def test_get_stock_intraday_kline(client: TestClient):
    response = client.get("/api/stocks/600519/kline/minute", params={"period": "1m"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"] == "1m"
    assert payload["bars"][0]["date"] == "2026-07-06 09:31:00"
    assert payload["bars"][1]["close"] == 101.5


def test_get_stock_intraday_kline_rejects_unsupported_period(client: TestClient):
    response = client.get("/api/stocks/600519/kline/minute", params={"period": "2m"})

    assert response.status_code == 400
    assert "1m、5m、15m、30m、60m" in response.json()["detail"]


def test_get_stock_quote(client: TestClient):
    response = client.get("/api/stocks/600519/quote")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_price"] == 105.0
    assert payload["change_amount"] == 2.0


def test_get_stock_live_quote(client: TestClient):
    response = client.get("/api/stocks/600519/quote/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_price"] == 108.0
    assert payload["change_percent"] == 2.86
    assert payload["is_live"] is True
    assert payload["source"] == "test_live"
    assert "quote_time" in payload
    assert payload["is_stale"] is False
    assert payload["cache_age_seconds"] == 0


def test_get_stock_live_quote_returns_stale_cache_when_provider_fails(
    client: TestClient,
    monkeypatch,
):
    calls = {"count": 0}

    def flaky_live_quote(code: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "code": code,
                "name": "贵州茅台",
                "latest_price": 108.0,
                "change_amount": 3.0,
                "change_percent": 2.86,
                "open": 104.0,
                "high": 109.0,
                "low": 103.0,
                "pre_close": 105.0,
                "volume": 1500.0,
                "amount": 150000.0,
                "turnover_rate": 1.8,
                "trade_date": date(2026, 7, 2),
                "quote_time": None,
                "source": "test_live",
            }
        raise RealtimeQuoteDataSourceError("provider down")

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_live_quote",
        flaky_live_quote,
    )

    first = client.get("/api/stocks/600519/quote/live", params={"refresh": "true"})
    second = client.get("/api/stocks/600519/quote/live", params={"refresh": "true"})

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()
    assert payload["latest_price"] == 108.0
    assert payload["is_stale"] is True
    assert payload["cache_age_seconds"] >= 0


def test_get_stock_live_quote_uses_cache_within_ttl(
    client: TestClient,
    monkeypatch,
):
    calls = {"count": 0}

    def counted_live_quote(code: str):
        calls["count"] += 1
        return {
            "code": code,
            "name": "贵州茅台",
            "latest_price": 108.0 + calls["count"],
            "change_amount": 3.0,
            "change_percent": 2.86,
            "open": 104.0,
            "high": 109.0,
            "low": 103.0,
            "pre_close": 105.0,
            "volume": 1500.0,
            "amount": 150000.0,
            "turnover_rate": 1.8,
            "trade_date": date(2026, 7, 2),
            "quote_time": None,
            "source": "test_live",
        }

    monkeypatch.setattr(
        "backend.app.services.stock_service.fetch_live_quote",
        counted_live_quote,
    )

    first = client.get("/api/stocks/600519/quote/live")
    second = client.get("/api/stocks/600519/quote/live")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["latest_price"] == 109.0
    assert second.json()["latest_price"] == 109.0
    assert second.json()["cache_age_seconds"] >= 0
    assert calls["count"] == 1


def test_get_stock_position(client: TestClient):
    response = client.get("/api/stocks/600519/position", params={"window": 250})

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "600519"
    assert payload["sample_size"] == 2
    assert payload["position_score"] == 85.71
    assert payload["zone"] == "high_watch"
    assert payload["label"] == "高位观察区"


def test_get_stock_position_rejects_unsupported_window(client: TestClient):
    response = client.get("/api/stocks/600519/position", params={"window": 100})

    assert response.status_code == 400
    assert "250、750、1250" in response.json()["detail"]
