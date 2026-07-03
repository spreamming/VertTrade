from datetime import date

from pydantic import BaseModel, Field


class StockSummary(BaseModel):
    code: str
    name: str
    exchange: str


class KlineBar(BaseModel):
    date: date
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


class KlineResponse(BaseModel):
    code: str
    name: str
    period: str = "daily"
    bars: list[KlineBar] = Field(default_factory=list)
