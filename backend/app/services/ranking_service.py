import math
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Callable

import requests
from pandas import DataFrame

from ..collectors.ranking_collector import (
    RankingDataSourceError,
    fetch_sector_rankings,
    fetch_stock_moneyflow_rankings,
    fetch_stock_spot_rankings,
)
from ..collectors.sector_collector import SectorDataSourceError
from ..schemas.ranking import DailyReviewResponse, RankingGroup, RankingItem


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _items_from_frame(frame: DataFrame, limit: int) -> list[RankingItem]:
    rows = frame.head(limit).to_dict(orient="records")
    return [
        RankingItem(**{key: _clean_value(value) for key, value in row.items()})
        for row in rows
    ]


class RankingService:
    _STOCK_SOURCE_TIMEOUT_SECONDS = 12
    _CACHE_TTL_SECONDS = 60
    _cache: dict[tuple[int, bool], tuple[float, DailyReviewResponse]] = {}

    def get_daily_review(
        self,
        limit: int = 10,
        include_stock: bool = True,
    ) -> DailyReviewResponse:
        cache_key = (limit, include_stock)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            return cached

        sector_frame, sector_error = self._load_sector_frame()

        if include_stock:
            executor = ThreadPoolExecutor(max_workers=2)
            try:
                futures = {
                    "stock": executor.submit(self._load_stock_frame),
                    "moneyflow": executor.submit(self._load_moneyflow_frame),
                }
                done, _ = wait(
                    futures.values(),
                    timeout=self._STOCK_SOURCE_TIMEOUT_SECONDS,
                )
                stock_frame, stock_error = self._future_result(
                    futures["stock"],
                    done,
                    "暂时无法获取股票行情排行，请稍后重试。",
                )
                moneyflow_frame, moneyflow_error = self._future_result(
                    futures["moneyflow"],
                    done,
                    "暂时无法获取个股资金流排行，请稍后重试。",
                )
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        else:
            stock_frame = None
            moneyflow_frame = None
            stock_error = "已按请求跳过全市场个股排行。"
            moneyflow_error = "已按请求跳过个股资金流排行。"

        groups: list[RankingGroup] = []
        if include_stock:
            groups.extend(
                self._build_stock_groups(
                    stock_frame=stock_frame,
                    stock_error=stock_error,
                    moneyflow_frame=moneyflow_frame,
                    moneyflow_error=moneyflow_error,
                    limit=limit,
                )
            )

        groups.extend(
            self._build_sector_groups(
                sector_frame=sector_frame,
                sector_error=sector_error,
                limit=limit,
            )
        )

        available_count = sum(1 for group in groups if group.items)
        cached_fallback = self._latest_cached_response(cache_key)
        if available_count == 0 and cached_fallback is not None:
            return self._with_cache_note(cached_fallback, stale=True)

        notes = [
            "排行榜用于每日观察市场强弱和资金方向，不构成交易建议。",
            "默认展示个股榜和板块榜；单个数据源失败时只影响对应榜单。",
            f"当前可用榜单 {available_count} / {len(groups)} 个；数据源不可用时会显示局部提示。",
        ]
        response = DailyReviewResponse(groups=groups, notes=notes)
        if available_count == len(groups):
            self._cache[cache_key] = (time.monotonic(), response)
        return response

    def _get_cached_response(
        self,
        cache_key: tuple[int, bool],
    ) -> DailyReviewResponse | None:
        cached = self._cache.get(cache_key)
        if cached is None:
            return None

        cached_at, response = cached
        if time.monotonic() - cached_at > self._CACHE_TTL_SECONDS:
            return None
        return self._with_cache_note(response, stale=False)

    def _latest_cached_response(
        self,
        cache_key: tuple[int, bool],
    ) -> DailyReviewResponse | None:
        cached = self._cache.get(cache_key)
        return cached[1] if cached else None

    def _with_cache_note(
        self,
        response: DailyReviewResponse,
        stale: bool,
    ) -> DailyReviewResponse:
        cache_note = (
            "当前显示上一份可用排行榜缓存；实时刷新暂不可用。"
            if stale
            else "当前显示 60 秒内的排行榜缓存，避免重复请求外部数据源。"
        )
        notes = [note for note in response.notes if "排行榜缓存" not in note]
        return DailyReviewResponse(groups=response.groups, notes=[*notes, cache_note])

    def _build_stock_groups(
        self,
        stock_frame: DataFrame | None,
        stock_error: str | None,
        moneyflow_frame: DataFrame | None,
        moneyflow_error: str | None,
        limit: int,
    ) -> list[RankingGroup]:
        return [
            self._stock_group(
                key="stock_gainers",
                title="个股涨幅榜",
                sorter=lambda frame: frame.sort_values(
                    "change_percent",
                    ascending=False,
                ),
                limit=limit,
                frame=stock_frame,
                error=stock_error,
            ),
            self._stock_group(
                key="stock_losers",
                title="个股跌幅榜",
                sorter=lambda frame: frame.sort_values(
                    "change_percent",
                    ascending=True,
                ),
                limit=limit,
                frame=stock_frame,
                error=stock_error,
            ),
            self._stock_group(
                key="stock_amount",
                title="成交额榜",
                sorter=lambda frame: frame.sort_values(
                    "amount",
                    ascending=False,
                ),
                limit=limit,
                frame=stock_frame,
                error=stock_error,
            ),
            self._stock_group(
                key="stock_turnover",
                title="换手率榜",
                sorter=lambda frame: frame.sort_values(
                    "turnover_rate",
                    ascending=False,
                ),
                limit=limit,
                frame=stock_frame,
                error=stock_error,
            ),
            self._moneyflow_group(
                key="stock_money_inflow",
                title="个股主力净流入榜",
                ascending=False,
                limit=limit,
                frame=moneyflow_frame,
                error=moneyflow_error,
            ),
            self._moneyflow_group(
                key="stock_money_outflow",
                title="个股主力净流出榜",
                ascending=True,
                limit=limit,
                frame=moneyflow_frame,
                error=moneyflow_error,
            ),
        ]

    def _build_sector_groups(
        self,
        sector_frame: DataFrame | None,
        sector_error: str | None,
        limit: int,
    ) -> list[RankingGroup]:
        return [
            self._sector_group(
                key="sector_gainers",
                title="板块涨幅榜",
                sorter=lambda frame: frame.sort_values(
                    "change_percent",
                    ascending=False,
                ),
                limit=limit,
                frame=sector_frame,
                error=sector_error,
            ),
            self._sector_group(
                key="sector_moneyflow",
                title="板块资金流榜",
                sorter=lambda frame: frame.sort_values(
                    "main_net_inflow",
                    ascending=False,
                ),
                limit=limit,
                frame=sector_frame,
                error=sector_error,
            ),
        ]

    def _future_result(self, future, done, timeout_message: str):
        if future not in done:
            return None, timeout_message
        return future.result()

    def _load_stock_frame(self) -> tuple[DataFrame | None, str | None]:
        try:
            return fetch_stock_spot_rankings(), None
        except (requests.RequestException, RankingDataSourceError, ValueError, KeyError):
            return None, "暂时无法获取股票行情排行，请稍后重试。"

    def _load_moneyflow_frame(self) -> tuple[DataFrame | None, str | None]:
        try:
            return fetch_stock_moneyflow_rankings(), None
        except (requests.RequestException, RankingDataSourceError, ValueError, KeyError):
            return None, "暂时无法获取个股资金流排行，请稍后重试。"

    def _load_sector_frame(self) -> tuple[DataFrame | None, str | None]:
        try:
            return fetch_sector_rankings(), None
        except (
            requests.RequestException,
            RankingDataSourceError,
            SectorDataSourceError,
            ValueError,
            KeyError,
        ):
            return None, "暂时无法获取板块排行，请稍后重试。"

    def _stock_group(
        self,
        key: str,
        title: str,
        sorter: Callable[[DataFrame], DataFrame],
        limit: int,
        frame: DataFrame | None,
        error: str | None,
    ) -> RankingGroup:
        try:
            if frame is None:
                raise RankingDataSourceError(error or "stock source unavailable")
            sorted_frame = sorter(frame)
            return RankingGroup(
                key=key,
                title=title,
                source=frame.attrs.get("source", "akshare_em"),
                items=_items_from_frame(sorted_frame, limit),
            )
        except (requests.RequestException, RankingDataSourceError, ValueError, KeyError):
            return RankingGroup(
                key=key,
                title=title,
                source="akshare_em",
                error=f"暂时无法获取{title}，请稍后重试。",
            )

    def _moneyflow_group(
        self,
        key: str,
        title: str,
        ascending: bool,
        limit: int,
        frame: DataFrame | None,
        error: str | None,
    ) -> RankingGroup:
        try:
            if frame is None:
                raise RankingDataSourceError(error or "moneyflow source unavailable")
            sorted_frame = frame.sort_values("main_net_inflow", ascending=ascending)
            return RankingGroup(
                key=key,
                title=title,
                source=frame.attrs.get("source", "akshare_em"),
                items=_items_from_frame(sorted_frame, limit),
            )
        except (requests.RequestException, RankingDataSourceError, ValueError, KeyError):
            return RankingGroup(
                key=key,
                title=title,
                source="akshare_em",
                error=f"暂时无法获取{title}，请稍后重试。",
            )

    def _sector_group(
        self,
        key: str,
        title: str,
        sorter: Callable[[DataFrame], DataFrame],
        limit: int,
        frame: DataFrame | None,
        error: str | None,
    ) -> RankingGroup:
        try:
            if frame is None:
                raise RankingDataSourceError(error or "sector source unavailable")
            sorted_frame = sorter(frame)
            return RankingGroup(
                key=key,
                title=title,
                source=frame.attrs.get("source", "akshare_em"),
                items=_items_from_frame(sorted_frame, limit),
            )
        except (
            requests.RequestException,
            RankingDataSourceError,
            SectorDataSourceError,
            ValueError,
            KeyError,
        ):
            return RankingGroup(
                key=key,
                title=title,
                source=None,
                error=f"暂时无法获取{title}，请稍后重试。",
            )
