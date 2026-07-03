from fastapi import APIRouter, Query

from ..schemas.sector import SectorDetailResponse, SectorListResponse
from ..services.sector_service import SectorService


router = APIRouter(prefix="/api/sectors", tags=["sectors"])


def get_sector_service() -> SectorService:
    return SectorService()


@router.get("/industries", response_model=SectorListResponse)
def list_industry_sectors():
    return get_sector_service().list_industry_sectors()


@router.get("/industries/{code}", response_model=SectorDetailResponse)
def get_industry_sector(
    code: str,
    name: str = Query(default=""),
):
    return get_sector_service().get_industry_sector(code=code, name=name or code)
