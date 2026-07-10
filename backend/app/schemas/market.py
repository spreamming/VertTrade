from datetime import datetime

from pydantic import BaseModel, Field


class MarketIndexSummary(BaseModel):
    code: str
    name: str
    exchange: str
    latest_price: float
    change_amount: float | None = None
    change_percent: float | None = None
    volume: float | None = None
    amount: float | None = None
    quote_time: datetime | None = None
    source: str = "tencent"


class MarketBreadthSummary(BaseModel):
    rising_count: int | None = None
    falling_count: int | None = None
    flat_count: int | None = None
    limit_up_count: int | None = None
    limit_down_count: int | None = None
    suspended_count: int | None = None
    activity_ratio: float | None = None
    as_of: datetime | None = None
    source: str = "legu"


class MarketOverviewResponse(BaseModel):
    indices: list[MarketIndexSummary] = Field(default_factory=list)
    breadth: MarketBreadthSummary | None = None
    source: str | None = None
    cache_time: datetime | None = None
    is_stale: bool = False
    cache_age_seconds: float | None = None
    notes: list[str] = Field(default_factory=list)
    error: str | None = None
