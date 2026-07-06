from pydantic import BaseModel, Field


class RankingItem(BaseModel):
    code: str | None = None
    name: str
    exchange: str | None = None
    latest_price: float | None = None
    change_percent: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    main_net_inflow: float | None = None
    leading_stock: str | None = None


class RankingGroup(BaseModel):
    key: str
    title: str
    source: str | None = None
    items: list[RankingItem] = Field(default_factory=list)
    error: str | None = None


class DailyReviewResponse(BaseModel):
    groups: list[RankingGroup] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
