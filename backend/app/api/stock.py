from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.stock import (
    KlineResponse,
    MoneyflowResponse,
    StockPosition,
    StockQuote,
    StockSummary,
    TimeShareResponse,
)
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


@router.get("/{code}/kline/minute", response_model=KlineResponse)
def get_stock_intraday_kline(
    code: str,
    period: str = Query(default="1m"),
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_intraday_kline(code, period=period, refresh=refresh)


@router.get("/{code}/timeshare", response_model=TimeShareResponse)
def get_stock_timeshare(
    code: str,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_timeshare(code, refresh=refresh)


@router.get("/{code}/quote", response_model=StockQuote)
def get_stock_quote(
    code: str,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_quote(code, refresh=refresh)


@router.get("/{code}/quote/live", response_model=StockQuote)
def get_stock_live_quote(
    code: str,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_live_quote(code, refresh=refresh)


@router.get("/{code}/position", response_model=StockPosition)
def get_stock_position(
    code: str,
    window: int = Query(default=250),
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_position(code, window=window, refresh=refresh)


@router.get("/{code}/moneyflow", response_model=MoneyflowResponse)
def get_stock_moneyflow(
    code: str,
    start: date | None = None,
    end: date | None = None,
    refresh: bool = False,
    service: StockService = Depends(get_stock_service),
):
    return service.get_moneyflow(code, start=start, end=end, refresh=refresh)
