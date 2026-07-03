from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.collectors import moneyflow_collector
from backend.app.collectors.moneyflow_collector import MoneyflowDataSourceError
from backend.app.database import Base, get_db
from backend.app.main import app


def _fake_moneyflow_frame() -> pd.DataFrame:
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
        "backend.app.services.stock_service.fetch_stock_moneyflow",
        lambda code, exchange=None: _fake_moneyflow_frame(),
    )

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_stock_moneyflow(client: TestClient):
    response = client.get("/api/stocks/600519/moneyflow")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "600519"
    assert payload["source"] == "akshare_em"
    assert len(payload["bars"]) == 2
    assert payload["bars"][0]["main_net_inflow"] == 100000000.0
    assert payload["bars"][1]["main_net_ratio"] == -2.1


def test_watchlist_includes_moneyflow_summary(client: TestClient):
    client.post("/api/watchlist", json={"code": "600519"})
    payload = client.get("/api/watchlist").json()

    assert payload[0]["main_net_inflow"] == -50000000.0
    assert payload[0]["main_net_ratio"] == -2.1
    assert payload[0]["moneyflow_date"] == "2026-07-02"


def test_moneyflow_collector_validates_required_columns(monkeypatch):
    def fake_source(stock: str, market: str) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "日期": "2026-07-02",
                    "主力净流入-净额": 100.0,
                }
            ]
        )

    monkeypatch.setattr(
        moneyflow_collector.ak,
        "stock_individual_fund_flow",
        fake_source,
    )

    with pytest.raises(MoneyflowDataSourceError, match="资金流数据源缺少字段"):
        moneyflow_collector.fetch_stock_moneyflow("600519", "SH")
