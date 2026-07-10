import math
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date, datetime, timedelta
from typing import Any

import requests
from fastapi import HTTPException

from ..collectors.sector_collector import (
    SectorDataSourceError,
    fetch_industry_constituents,
    fetch_industry_sectors,
)
from ..collectors.sector_kline_collector import fetch_sector_kline
from ..collectors.sector_moneyflow_collector import fetch_sector_moneyflow
from ..schemas.sector import (
    SectorConstituent,
    SectorDetailResponse,
    SectorKlineResponse,
    SectorListResponse,
    SectorMoneyflowResponse,
    SectorSummary,
)
from ..schemas.stock import KlineBar, MoneyflowBar


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _rows_to_dicts(rows: list[dict]) -> list[dict]:
    return [
        {key: _clean_value(value) for key, value in row.items()}
        for row in rows
    ]


class SectorService:
    _SOURCE_TIMEOUT_SECONDS = 8
    _CACHE_TTL_SECONDS = 60
    _DETAIL_CACHE_TTL_SECONDS = 300
    _CHART_CACHE_TTL_SECONDS = 60
    _sector_list_cache: tuple[float, SectorListResponse] | None = None
    _sector_detail_cache: dict[tuple[str, str], tuple[float, SectorDetailResponse]] = {}
    _sector_kline_cache: dict[tuple[str, str], tuple[float, SectorKlineResponse]] = {}
    _sector_moneyflow_cache: dict[tuple[str, str], tuple[float, SectorMoneyflowResponse]] = {}

    @classmethod
    def clear_chart_cache(cls) -> None:
        cls._sector_kline_cache.clear()
        cls._sector_moneyflow_cache.clear()

    @staticmethod
    def _with_chart_cache_metadata(
        response: SectorKlineResponse | SectorMoneyflowResponse,
        cached_at: datetime,
        now: datetime,
        *,
        is_stale: bool,
    ) -> SectorKlineResponse | SectorMoneyflowResponse:
        cache_age = (now - cached_at).total_seconds()
        return response.model_copy(
            update={
                "cache_time": cached_at,
                "is_stale": is_stale,
                "cache_age_seconds": cache_age,
            }
        )

    def list_industry_sectors(self) -> SectorListResponse:
        cached = self._get_cached_sector_list()
        if cached is not None:
            return cached

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(fetch_industry_sectors)
            frame = future.result(timeout=self._SOURCE_TIMEOUT_SECONDS)
        except (
            requests.RequestException,
            SectorDataSourceError,
            TimeoutError,
            ValueError,
        ) as exc:
            fallback = self._latest_cached_sector_list()
            if fallback is not None:
                return fallback
            raise HTTPException(
                status_code=503,
                detail="暂时无法从数据源获取行业板块数据，请稍后重试。",
            ) from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        rows = _rows_to_dicts(frame.to_dict(orient="records"))
        response = SectorListResponse(
            sectors=[SectorSummary(**row) for row in rows],
            source=frame.attrs.get("source", "akshare_em"),
        )
        self._sector_list_cache = (time.monotonic(), response)
        return response

    def _get_cached_sector_list(self) -> SectorListResponse | None:
        cached = self._sector_list_cache
        if cached is None:
            return None
        cached_at, response = cached
        if time.monotonic() - cached_at > self._CACHE_TTL_SECONDS:
            return None
        return response

    def _latest_cached_sector_list(self) -> SectorListResponse | None:
        cached = self._sector_list_cache
        return cached[1] if cached else None

    def get_industry_sector(self, code: str, name: str) -> SectorDetailResponse:
        cache_key = (code, name)
        cached = self._get_cached_sector_detail(cache_key)
        if cached is not None:
            return cached

        errors: list[Exception] = []
        candidates = []
        for candidate in (name, code):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        frame = None
        for candidate in candidates:
            try:
                frame = fetch_industry_constituents(candidate)
                break
            except (
                requests.RequestException,
                SectorDataSourceError,
                ValueError,
                IndexError,
            ) as exc:
                errors.append(exc)

        if frame is None:
            message = "; ".join(
                f"{type(error).__name__}: {str(error).splitlines()[0]}"
                for error in errors
            )
            raise HTTPException(
                status_code=503,
                detail="暂时无法从数据源获取板块成分股，请稍后重试。",
                headers={"X-Data-Source-Error": message[:500]},
            )

        rows = _rows_to_dicts(frame.to_dict(orient="records"))
        response = SectorDetailResponse(
            code=code,
            name=name,
            constituents=[SectorConstituent(**row) for row in rows],
            source=frame.attrs.get("source", "akshare_em"),
        )
        self._sector_detail_cache[cache_key] = (time.monotonic(), response)
        return response

    def get_industry_sector_kline(
        self,
        code: str,
        name: str,
        refresh: bool = False,
    ) -> SectorKlineResponse:
        sector_name = name or code
        cache_key = (code, sector_name)
        cached = self._sector_kline_cache.get(cache_key)
        now = datetime.now()
        if not refresh and cached:
            cached_at_mono, cached_response = cached
            cache_age = time.monotonic() - cached_at_mono
            if cache_age <= self._CHART_CACHE_TTL_SECONDS:
                cached_time = cached_response.cache_time or now
                return self._with_chart_cache_metadata(
                    cached_response,
                    cached_time,
                    now,
                    is_stale=False,
                )

        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        try:
            frame, source = fetch_sector_kline(
                sector_name,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )
        except (requests.RequestException, SectorDataSourceError, ValueError) as exc:
            if cached:
                cached_at_mono, cached_response = cached
                cached_time = cached_response.cache_time or now
                return self._with_chart_cache_metadata(
                    cached_response,
                    cached_time,
                    now,
                    is_stale=True,
                )
            raise HTTPException(
                status_code=503,
                detail=f"暂时无法从数据源获取 {sector_name} 的板块 K 线，请稍后重试。",
            ) from exc

        bars = [
            KlineBar(
                date=row["trade_date"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                amount=row["amount"],
                turnover_rate=row["turnover_rate"],
            )
            for row in frame.to_dict(orient="records")
        ]
        response = SectorKlineResponse(
            code=code,
            name=sector_name,
            bars=bars,
            source=source,
            cache_time=now,
            is_stale=False,
            cache_age_seconds=0,
        )
        self._sector_kline_cache[cache_key] = (time.monotonic(), response)
        return response

    def get_industry_sector_moneyflow(
        self,
        code: str,
        name: str,
        refresh: bool = False,
    ) -> SectorMoneyflowResponse:
        sector_name = name or code
        cache_key = (code, sector_name)
        cached = self._sector_moneyflow_cache.get(cache_key)
        now = datetime.now()
        if not refresh and cached:
            cached_at_mono, cached_response = cached
            cache_age = time.monotonic() - cached_at_mono
            if cache_age <= self._CHART_CACHE_TTL_SECONDS:
                cached_time = cached_response.cache_time or now
                return self._with_chart_cache_metadata(
                    cached_response,
                    cached_time,
                    now,
                    is_stale=False,
                )

        try:
            frame = fetch_sector_moneyflow(sector_name)
        except (requests.RequestException, SectorDataSourceError, ValueError) as exc:
            if cached:
                cached_at_mono, cached_response = cached
                cached_time = cached_response.cache_time or now
                return self._with_chart_cache_metadata(
                    cached_response,
                    cached_time,
                    now,
                    is_stale=True,
                )
            raise HTTPException(
                status_code=503,
                detail=f"暂时无法从数据源获取 {sector_name} 的板块资金流，请稍后重试。",
            ) from exc

        bars = [
            MoneyflowBar(
                date=row["trade_date"],
                main_net_inflow=row["main_net_inflow"],
                main_net_ratio=row["main_net_ratio"],
                super_large_net_inflow=None,
                large_net_inflow=None,
                medium_net_inflow=None,
                small_net_inflow=None,
            )
            for row in frame.to_dict(orient="records")
        ]
        response = SectorMoneyflowResponse(
            code=code,
            name=sector_name,
            bars=bars,
            source="eastmoney",
            cache_time=now,
            is_stale=False,
            cache_age_seconds=0,
        )
        self._sector_moneyflow_cache[cache_key] = (time.monotonic(), response)
        return response

    def _get_cached_sector_detail(
        self,
        cache_key: tuple[str, str],
    ) -> SectorDetailResponse | None:
        cached = self._sector_detail_cache.get(cache_key)
        if cached is None:
            return None
        cached_at, response = cached
        if time.monotonic() - cached_at > self._DETAIL_CACHE_TTL_SECONDS:
            return None
        return response
