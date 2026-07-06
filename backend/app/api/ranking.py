from fastapi import APIRouter, Query

from ..schemas.ranking import DailyReviewResponse
from ..services.ranking_service import RankingService


router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get("/daily-review", response_model=DailyReviewResponse)
def get_daily_review(
    limit: int = Query(default=10, ge=3, le=20),
    include_stock: bool = True,
):
    return RankingService().get_daily_review(
        limit=limit,
        include_stock=include_stock,
    )
