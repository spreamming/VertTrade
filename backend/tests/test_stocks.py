from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app


@pytest.fixture
def client(monkeypatch):
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
