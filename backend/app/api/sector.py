from fastapi import APIRouter, Query

from ..schemas.sector import SectorDetailResponse, SectorKlineResponse, SectorListResponse, SectorMoneyflowResponse
from ..services.sector_service import SectorService


router = APIRouter(prefix="/api/sectors", tags=["sectors"])


def get_sector_service() -> SectorService:
    return SectorService()


@router.get("/industries", response_model=SectorListResponse)
def list_industry_sectors():
    return get_sector_service().list_industry_sectors()


@router.get("/industries/{code}/kline", response_model=SectorKlineResponse)
def get_industry_sector_kline(
    code: str,
    name: str = Query(default=""),
    refresh: bool = False,
):
    return get_sector_service().get_industry_sector_kline(
        code=code,
        name=name or code,
        refresh=refresh,
    )


@router.get("/industries/{code}/moneyflow", response_model=SectorMoneyflowResponse)
def get_industry_sector_moneyflow(
    code: str,
    name: str = Query(default=""),
    refresh: bool = False,
):
    return get_sector_service().get_industry_sector_moneyflow(
        code=code,
        name=name or code,
        refresh=refresh,
    )


@router.get("/industries/{code}", response_model=SectorDetailResponse)
def get_industry_sector(
    code: str,
    name: str = Query(default=""),
):
    return get_sector_service().get_industry_sector(code=code, name=name or code)
