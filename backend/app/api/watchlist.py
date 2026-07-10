from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.watchlist import DashboardResponse, WatchlistCreate, WatchlistItemResponse
from ..services.watchlist_service import WatchlistService

router = APIRouter(tags=["watchlist"])


def get_watchlist_service(db: Session = Depends(get_db)) -> WatchlistService:
    return WatchlistService(db)


@router.get("/api/watchlist", response_model=list[WatchlistItemResponse])
def list_watchlist(service: WatchlistService = Depends(get_watchlist_service)):
    return service.list_items()


@router.post(
    "/api/watchlist",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_watchlist_item(
    payload: WatchlistCreate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.add_item(payload)


@router.delete("/api/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    item_id: int,
    service: WatchlistService = Depends(get_watchlist_service),
):
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    refresh: bool = False,
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.get_dashboard(refresh=refresh)
