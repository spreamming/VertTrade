from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    group_name: str = Field(default="默认", min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=255)


class WatchlistItemResponse(BaseModel):
    id: int
    code: str
    name: str
    exchange: str
    group_name: str
    sort_order: int
    note: str | None = None
    latest_price: float | None = None
    change_amount: float | None = None
    change_percent: float | None = None
    trade_date: str | None = None
    quote_error: str | None = None
    position_score: float | None = None
    position_label: str | None = None
    position_window: int | None = None
    position_error: str | None = None
    created_at: datetime


class DashboardResponse(BaseModel):
    watchlist_count: int
    watchlist_summary: list[WatchlistItemResponse]
    indices: list[dict] = Field(default_factory=list)
    market_notes: list[str] = Field(default_factory=list)
