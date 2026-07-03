from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import WatchlistItem
from ..repositories.stock_repo import StockRepository
from ..repositories.watchlist_repo import WatchlistRepository
from ..schemas.stock import StockQuote
from ..schemas.watchlist import DashboardResponse, WatchlistCreate, WatchlistItemResponse
from .stock_service import StockService


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db
        self.watchlist_repo = WatchlistRepository(db)
        self.stock_repo = StockRepository(db)
        self.stock_service = StockService(db)

    def list_items(self) -> list[WatchlistItemResponse]:
        self.stock_service.ensure_stock_catalog()
        return [self._to_response(item) for item in self.watchlist_repo.list_items()]

    def add_item(self, payload: WatchlistCreate) -> WatchlistItemResponse:
        self.stock_service.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(payload.code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {payload.code}")

        item = self.watchlist_repo.add(
            code=payload.code,
            group_name=payload.group_name,
            note=payload.note,
        )
        return self._to_response(item)

    def delete_item(self, item_id: int) -> None:
        if not self.watchlist_repo.delete(item_id):
            raise HTTPException(status_code=404, detail=f"未找到自选股记录 {item_id}")

    def get_dashboard(self) -> DashboardResponse:
        items = self.list_items()
        return DashboardResponse(
            watchlist_count=self.watchlist_repo.count(),
            watchlist_summary=items,
            indices=[],
            market_notes=[
                "主要指数、市场涨跌家数和板块概览将在后续阶段接入。",
            ],
        )

    def _to_response(self, item: WatchlistItem) -> WatchlistItemResponse:
        stock = self.stock_repo.get_by_code(item.code)
        quote: StockQuote | None = None
        quote_error: str | None = None

        try:
            quote = self.stock_service.get_quote(item.code)
        except HTTPException as exc:
            quote_error = str(exc.detail)

        return WatchlistItemResponse(
            id=item.id,
            code=item.code,
            name=stock.name if stock else item.code,
            exchange=stock.exchange if stock else "UNKNOWN",
            group_name=item.group_name,
            sort_order=item.sort_order,
            note=item.note,
            latest_price=quote.latest_price if quote else None,
            change_amount=quote.change_amount if quote else None,
            change_percent=quote.change_percent if quote else None,
            trade_date=quote.trade_date.isoformat() if quote else None,
            quote_error=quote_error,
            created_at=item.created_at,
        )
