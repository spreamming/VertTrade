from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.market_overview_service import MarketOverviewService


@pytest.fixture
def client():
    MarketOverviewService.clear_cache()
    with TestClient(app) as test_client:
        yield test_client
    MarketOverviewService.clear_cache()


@pytest.fixture
def fake_market_data(monkeypatch):
    def fake_indices():
        return [
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
            },
            {
                "code": "399001",
                "name": "深证成指",
                "exchange": "SZ",
                "latest_price": 14887.99,
                "change_amount": -51.74,
                "change_percent": -0.35,
                "volume": 445168332.0,
                "amount": 906276500000.0,
                "quote_time": datetime(2026, 7, 9, 11, 30),
                "source": "tencent",
            },
        ]

    def fake_breadth():
        return {
            "rising_count": 799,
            "falling_count": 4333,
            "flat_count": 62,
            "limit_up_count": 36,
            "limit_down_count": 20,
            "suspended_count": 9,
            "activity_ratio": 15.36,
            "as_of": datetime(2026, 7, 9, 11, 30),
            "source": "legu",
        }

    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_major_indices",
        fake_indices,
    )
    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_market_breadth",
        fake_breadth,
    )


def test_get_market_overview(client: TestClient, fake_market_data):
    response = client.get("/api/market/overview")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["indices"]) == 2
    assert payload["indices"][0]["name"] == "上证指数"
    assert payload["breadth"]["rising_count"] == 799
    assert payload["is_stale"] is False
    assert payload["notes"]


def test_get_market_overview_uses_cache_within_ttl(
    client: TestClient,
    fake_market_data,
    monkeypatch,
):
    calls = {"count": 0}

    def counted_indices():
        calls["count"] += 1
        return [
            {
                "code": "000001",
                "name": "上证指数",
                "exchange": "SH",
                "latest_price": 3952.49 + calls["count"],
                "change_amount": -18.39,
                "change_percent": -0.46,
                "volume": 330849707.0,
                "amount": 790773120000.0,
                "quote_time": datetime(2026, 7, 9, 11, 30),
                "source": "tencent",
            }
        ]

    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_major_indices",
        counted_indices,
    )

    first = client.get("/api/market/overview")
    second = client.get("/api/market/overview")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["indices"][0]["latest_price"] == 3953.49
    assert second.json()["indices"][0]["latest_price"] == 3953.49
    assert calls["count"] == 1


def test_get_market_overview_returns_stale_cache_when_indices_fail(
    client: TestClient,
    fake_market_data,
    monkeypatch,
):
    calls = {"count": 0}

    def flaky_indices():
        calls["count"] += 1
        if calls["count"] == 1:
            return [
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
            ]
        raise ValueError("provider down")

    monkeypatch.setattr(
        "backend.app.services.market_overview_service.fetch_major_indices",
        flaky_indices,
    )

    first = client.get("/api/market/overview", params={"refresh": "true"})
    second = client.get("/api/market/overview", params={"refresh": "true"})

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()
    assert payload["indices"][0]["latest_price"] == 3952.49
    assert payload["is_stale"] is True
    assert payload["error"]
