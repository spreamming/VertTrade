from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.stock import KlineResponse, StockPosition, StockQuote, StockSummary
from ..services.stock_service import StockService

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


def get_stock_service(db: Session = Depends(get_db)) -> StockService:
    return StockService(db)


@router.get("/search", response_model=list[StockSummary])
def search_stocks(
    keyword: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    service: StockService = Depends(get_stock_service),
):
    return service.search_stocks(keyword, limit=limit)


@router.get("/{code}/kline", response_model=KlineResponse)
def get_stock_kline(
    code: str,
    start: date | None = None,
    end: date | None = None,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_kline(code, start=start, end=end, refresh=refresh)


@router.get("/{code}/quote", response_model=StockQuote)
def get_stock_quote(
    code: str,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_quote(code, refresh=refresh)


@router.get("/{code}/position", response_model=StockPosition)
def get_stock_position(
    code: str,
    window: int = Query(default=250),
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_position(code, window=window, refresh=refresh)
