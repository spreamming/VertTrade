from datetime import datetime

import requests

from ..collectors.market_overview_collector import (
    MarketOverviewDataSourceError,
    fetch_major_indices,
    fetch_market_breadth,
)
from ..schemas.market import (
    MarketBreadthSummary,
    MarketIndexSummary,
    MarketOverviewResponse,
)


class MarketOverviewService:
    _CACHE_TTL_SECONDS = 10
    _cache: tuple[datetime, MarketOverviewResponse] | None = None

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache = None

    def get_market_overview(self, refresh: bool = False) -> MarketOverviewResponse:
        now = datetime.now()
        cached = MarketOverviewService._cache
        if not refresh and cached:
            cached_at, cached_response = cached
            cache_age = (now - cached_at).total_seconds()
            if cache_age <= self._CACHE_TTL_SECONDS:
                return cached_response.model_copy(
                    update={
                        "cache_time": cached_at,
                        "is_stale": False,
                        "cache_age_seconds": cache_age,
                    }
                )

        notes: list[str] = []
        indices: list[MarketIndexSummary] = []
        breadth: MarketBreadthSummary | None = None
        error: str | None = None

        try:
            indices = [
                MarketIndexSummary(**item)
                for item in fetch_major_indices()
            ]
        except (requests.RequestException, MarketOverviewDataSourceError, ValueError) as exc:
            error = str(exc) if str(exc) else "暂时无法获取主要指数行情，请稍后重试。"
            cached = MarketOverviewService._cache
            if cached:
                cached_at, cached_response = cached
                return cached_response.model_copy(
                    update={
                        "cache_time": cached_at,
                        "is_stale": True,
                        "cache_age_seconds": (now - cached_at).total_seconds(),
                        "error": error,
                    }
                )

        try:
            breadth = MarketBreadthSummary(**fetch_market_breadth())
        except (requests.RequestException, ValueError):
            notes.append("市场涨跌家数暂时不可用，请稍后重试。")

        if indices:
            notes.append("主要指数来自腾讯行情；涨跌家数来自乐股网统计，仅作观察参考。")

        response = MarketOverviewResponse(
            indices=indices,
            breadth=breadth,
            source="tencent+legu" if indices and breadth else (indices[0].source if indices else None),
            cache_time=now,
            is_stale=False,
            cache_age_seconds=0,
            notes=notes,
            error=error if not indices else None,
        )
        if indices:
            MarketOverviewService._cache = (now, response)
        return response
