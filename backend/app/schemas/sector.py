from pydantic import BaseModel, Field


class SectorSummary(BaseModel):
    code: str
    name: str
    latest_price: float | None = None
    change_amount: float | None = None
    change_percent: float | None = None
    amount: float | None = None
    main_net_inflow: float | None = None
    market_value: float | None = None
    turnover_rate: float | None = None
    rising_count: int | None = None
    falling_count: int | None = None
    leading_stock: str | None = None
    leading_stock_change_percent: float | None = None


class SectorConstituent(BaseModel):
    code: str
    name: str
    exchange: str
    latest_price: float | None = None
    change_amount: float | None = None
    change_percent: float | None = None
    volume: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    pe_dynamic: float | None = None
    pb: float | None = None


class SectorListResponse(BaseModel):
    sectors: list[SectorSummary] = Field(default_factory=list)
    source: str = "akshare_em"


class SectorDetailResponse(BaseModel):
    code: str
    name: str
    constituents: list[SectorConstituent] = Field(default_factory=list)
    source: str = "akshare_em"
