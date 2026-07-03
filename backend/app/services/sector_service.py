import math
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
    def list_industry_sectors(self) -> SectorListResponse:
        try:
            frame = fetch_industry_sectors()
        except (requests.RequestException, SectorDataSourceError, ValueError) as exc:
            raise HTTPException(
                status_code=503,
                detail="暂时无法从数据源获取行业板块数据，请稍后重试。",
            ) from exc

        rows = _rows_to_dicts(frame.to_dict(orient="records"))
        return SectorListResponse(
            sectors=[SectorSummary(**row) for row in rows],
            source=frame.attrs.get("source", "akshare_em"),
        )

    def get_industry_sector(self, code: str, name: str) -> SectorDetailResponse:
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
        return SectorDetailResponse(
            code=code,
            name=name,
            constituents=[SectorConstituent(**row) for row in rows],
            source=frame.attrs.get("source", "akshare_em"),
        )
