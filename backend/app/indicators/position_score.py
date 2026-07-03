from dataclasses import dataclass
from datetime import date
from typing import Protocol


class PriceBar(Protocol):
    trade_date: date
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class PositionResult:
    trade_date: date
    latest_close: float
    rolling_low: float
    rolling_high: float
    position_score: float
    zone: str
    label: str
    sample_size: int


def calculate_position_score(bars: list[PriceBar], window: int) -> PositionResult | None:
    if not bars:
        return None

    sample = bars[-window:] if len(bars) > window else bars
    latest = sample[-1]
    rolling_low = min(bar.low for bar in sample)
    rolling_high = max(bar.high for bar in sample)

    if rolling_high == rolling_low:
        score = 50.0
    else:
        score = (latest.close - rolling_low) / (rolling_high - rolling_low) * 100

    clamped_score = max(0.0, min(100.0, round(score, 2)))
    zone, label = classify_position_zone(clamped_score)

    return PositionResult(
        trade_date=latest.trade_date,
        latest_close=latest.close,
        rolling_low=rolling_low,
        rolling_high=rolling_high,
        position_score=clamped_score,
        zone=zone,
        label=label,
        sample_size=len(sample),
    )


def classify_position_zone(score: float) -> tuple[str, str]:
    if score <= 10:
        return "deep_bottom", "深度底部区"
    if score <= 20:
        return "bottom_watch", "底部观察区"
    if score < 80:
        return "neutral", "中性区"
    if score < 90:
        return "high_watch", "高位观察区"
    return "top_risk", "顶部风险区"
