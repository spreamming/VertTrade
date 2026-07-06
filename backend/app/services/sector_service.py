import math
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

import requests
from fastapi import HTTPException

from ..collectors.sector_collector import (
    SectorDataSourceError,
    fetch_industry_constituents,
    fetch_industry_sectors,
)
from ..schemas.sector import (
    SectorConstituent,
    SectorDetailResponse,
    SectorListResponse,
    SectorSummary,
)


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
    _sector_list_cache: tuple[float, SectorListResponse] | None = None
    _sector_detail_cache: dict[tuple[str, str], tuple[float, SectorDetailResponse]] = {}

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
