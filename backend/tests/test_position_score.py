from datetime import date
from types import SimpleNamespace

import pytest

from backend.app.indicators.position_score import (
    calculate_position_score,
    classify_position_zone,
)


def _bar(day: int, *, low: float, high: float, close: float) -> SimpleNamespace:
    return SimpleNamespace(
        trade_date=date(2026, 1, day),
        low=low,
        high=high,
        close=close,
    )


def _bars_with_close(close: float, *, low: float = 0.0, high: float = 100.0, count: int = 5):
    return [_bar(day + 1, low=low, high=high, close=close) for day in range(count)]


@pytest.mark.parametrize(
    ("close", "expected_zone", "expected_label"),
    [
        (5.0, "deep_bottom", "深度底部区"),
        (10.0, "deep_bottom", "深度底部区"),
        (15.0, "bottom_watch", "底部观察区"),
        (20.0, "bottom_watch", "底部观察区"),
        (50.0, "neutral", "中性区"),
        (79.0, "neutral", "中性区"),
        (85.0, "high_watch", "高位观察区"),
        (89.0, "high_watch", "高位观察区"),
        (95.0, "top_risk", "顶部风险区"),
        (100.0, "top_risk", "顶部风险区"),
    ],
)
def test_classify_position_zone_boundaries(close, expected_zone, expected_label):
    score = (close / 100.0) * 100.0
    zone, label = classify_position_zone(score)

    assert zone == expected_zone
    assert label == expected_label


def test_calculate_position_score_flat_range_returns_neutral():
    bars = _bars_with_close(42.0, low=50.0, high=50.0)

    result = calculate_position_score(bars, window=5)

    assert result is not None
    assert result.position_score == 50.0
    assert result.zone == "neutral"
    assert result.label == "中性区"


def test_calculate_position_score_clamps_below_zero():
    bars = _bars_with_close(-10.0, low=0.0, high=100.0)

    result = calculate_position_score(bars, window=5)

    assert result is not None
    assert result.position_score == 0.0
    assert result.zone == "deep_bottom"


def test_calculate_position_score_clamps_above_hundred():
    bars = _bars_with_close(150.0, low=0.0, high=100.0)

    result = calculate_position_score(bars, window=5)

    assert result is not None
    assert result.position_score == 100.0
    assert result.zone == "top_risk"


def test_calculate_position_score_empty_bars_returns_none():
    assert calculate_position_score([], window=250) is None
