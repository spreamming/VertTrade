from datetime import date, timedelta

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..collectors.kline_collector import fetch_daily_kline
from ..collectors.stock_basic_collector import fetch_stock_list
from ..repositories.kline_repo import KlineRepository
from ..repositories.stock_repo import StockRepository
from ..schemas.stock import KlineBar, KlineResponse, StockQuote, StockSummary


class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_repo = StockRepository(db)
        self.kline_repo = KlineRepository(db)

    def ensure_stock_catalog(self) -> None:
        if self.stock_repo.count() > 0:
            return

        frame = fetch_stock_list()
        rows = frame.to_dict(orient="records")
        self.stock_repo.upsert_many(rows)

    def search_stocks(self, keyword: str, limit: int = 20) -> list[StockSummary]:
        self.ensure_stock_catalog()
        matches = self.stock_repo.search(keyword, limit=limit)
        return [
            StockSummary(code=stock.code, name=stock.name, exchange=stock.exchange)
            for stock in matches
        ]

    def get_kline(
        self,
        code: str,
        start: date | None = None,
        end: date | None = None,
        refresh: bool = False,
    ) -> KlineResponse:
        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=365))

        cached = self.kline_repo.get_range(code, start_date, end_date)
        if refresh or not cached:
            try:
                frame = fetch_daily_kline(code, start_date, end_date)
            except requests.RequestException as exc:
                if cached:
                    frame = None
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "暂时无法从数据源获取行情数据，"
                            "请检查网络连接后重试。"
                        ),
                    ) from exc
            else:
                if frame.empty:
                    if not cached:
                        raise HTTPException(
                            status_code=404,
                            detail=f"暂无 {code} 的 K 线数据",
                        )
                else:
                    rows = frame.to_dict(orient="records")
                    self.kline_repo.replace_range(code, rows)
                    cached = self.kline_repo.get_range(code, start_date, end_date)

        bars = [
            KlineBar(
                date=bar.trade_date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                amount=bar.amount,
                turnover_rate=bar.turnover_rate,
            )
            for bar in cached
        ]

        return KlineResponse(code=stock.code, name=stock.name, bars=bars)

    def get_quote(self, code: str, refresh: bool = False) -> StockQuote:
        kline = self.get_kline(code, refresh=refresh)
        if not kline.bars:
            raise HTTPException(status_code=404, detail=f"暂无 {code} 的行情摘要")

        latest = kline.bars[-1]
        previous = kline.bars[-2] if len(kline.bars) > 1 else None
        pre_close = previous.close if previous else None
        change_amount = latest.close - pre_close if pre_close is not None else None
        change_percent = (
            (change_amount / pre_close) * 100
            if pre_close not in (None, 0) and change_amount is not None
            else None
        )

        stock = self.stock_repo.get_by_code(code)
        return StockQuote(
            code=kline.code,
            name=kline.name,
            exchange=stock.exchange if stock else "UNKNOWN",
            latest_price=latest.close,
            change_amount=change_amount,
            change_percent=change_percent,
            open=latest.open,
            high=latest.high,
            low=latest.low,
            pre_close=pre_close,
            volume=latest.volume,
            amount=latest.amount,
            turnover_rate=latest.turnover_rate,
            trade_date=latest.date,
        )
