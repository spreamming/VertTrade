from datetime import date
from datetime import datetime

from pydantic import BaseModel, Field


class StockSummary(BaseModel):
    code: str
    name: str
    exchange: str


class KlineBar(BaseModel):
    date: date | str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    turnover_rate: float | None = None


class StockQuote(BaseModel):
    code: str
    name: str
    exchange: str
    latest_price: float
    change_amount: float | None = None
    change_percent: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    pre_close: float | None = None
    volume: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    trade_date: date
    source: str | None = None
    is_live: bool = False
    cache_time: datetime | None = None
    quote_time: datetime | None = None
    is_stale: bool = False
    cache_age_seconds: float | None = None


class KlineResponse(BaseModel):
    code: str
    name: str
    period: str = "daily"
    bars: list[KlineBar] = Field(default_factory=list)


class TimeSharePoint(BaseModel):
    time: str
    price: float
    average_price: float | None = None
    volume: float | None = None
    amount: float | None = None


class TimeShareResponse(BaseModel):
    code: str
    name: str
    source: str = "tencent"
    points: list[TimeSharePoint] = Field(default_factory=list)


class StockPosition(BaseModel):
    code: str
    name: str
    window: int
    sample_size: int
    trade_date: date
    latest_close: float
    rolling_low: float
    rolling_high: float
    position_score: float
    zone: str
    label: str


class MoneyflowBar(BaseModel):
    date: date
    main_net_inflow: float
    main_net_ratio: float | None = None
    super_large_net_inflow: float | None = None
    large_net_inflow: float | None = None
    medium_net_inflow: float | None = None
    small_net_inflow: float | None = None


class MoneyflowResponse(BaseModel):
    code: str
    name: str
    source: str = "akshare_em"
    bars: list[MoneyflowBar] = Field(default_factory=list)
