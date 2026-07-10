from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.market import MarketOverviewResponse
from ..services.market_overview_service import MarketOverviewService

router = APIRouter(prefix="/api/market", tags=["market"])

_market_overview_service = MarketOverviewService()


def get_market_overview_service() -> MarketOverviewService:
    return _market_overview_service


@router.get("/overview", response_model=MarketOverviewResponse)
def get_market_overview(
    refresh: bool = False,
    service: MarketOverviewService = Depends(get_market_overview_service),
):
    return service.get_market_overview(refresh=refresh)
