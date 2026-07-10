from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import WatchlistItem
from ..repositories.stock_repo import StockRepository
from ..repositories.watchlist_repo import WatchlistRepository
from ..schemas.stock import MoneyflowBar, StockPosition, StockQuote
from ..schemas.watchlist import DashboardResponse, WatchlistCreate, WatchlistItemResponse
from .market_overview_service import MarketOverviewService
from .stock_service import StockService


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db
        self.watchlist_repo = WatchlistRepository(db)
        self.stock_repo = StockRepository(db)
        self.stock_service = StockService(db)
        self.market_overview_service = MarketOverviewService()

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

    def get_dashboard(self, refresh: bool = False) -> DashboardResponse:
        items = self.list_items()
        market_overview = self.market_overview_service.get_market_overview(refresh=refresh)
        return DashboardResponse(
            watchlist_count=self.watchlist_repo.count(),
            watchlist_summary=items,
            market_overview=market_overview,
            indices=market_overview.indices,
            market_breadth=market_overview.breadth,
            market_notes=market_overview.notes,
        )

    def _to_response(self, item: WatchlistItem) -> WatchlistItemResponse:
        stock = self.stock_repo.get_by_code(item.code)
        quote: StockQuote | None = None
        quote_error: str | None = None
        position: StockPosition | None = None
        position_error: str | None = None
        latest_moneyflow: MoneyflowBar | None = None
        moneyflow_error: str | None = None

        try:
            quote, position = self.stock_service.get_quote_and_position(item.code)
        except HTTPException as exc:
            detail = str(exc.detail)
            quote_error = detail
            position_error = detail

        try:
            latest_moneyflow = self.stock_service.get_latest_moneyflow(item.code)
        except HTTPException as exc:
            moneyflow_error = str(exc.detail)

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
            position_score=position.position_score if position else None,
            position_label=position.label if position else None,
            position_window=position.window if position else None,
            position_error=position_error,
            main_net_inflow=latest_moneyflow.main_net_inflow if latest_moneyflow else None,
            main_net_ratio=latest_moneyflow.main_net_ratio if latest_moneyflow else None,
            moneyflow_date=(
                latest_moneyflow.date.isoformat() if latest_moneyflow else None
            ),
            moneyflow_error=moneyflow_error,
            created_at=item.created_at,
        )
