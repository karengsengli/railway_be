from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .service import DistanceCalculationService
from .schemas import DistanceCalculationRequest, DistanceCalculationResponse

router = APIRouter()

@router.post("/calculate", response_model=DistanceCalculationResponse)
async def calculate_distance_and_time(
    request: DistanceCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate distance and time between two stations
    """
    service = DistanceCalculationService(db)
    result = await service.calculate_distance_and_time(request)

    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)

    return result

@router.get("/calculate", response_model=DistanceCalculationResponse)
async def calculate_distance_and_time_get(
    from_station_id: int = Query(..., description="ID of the starting station"),
    to_station_id: int = Query(..., description="ID of the destination station"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate distance and time between two stations using query parameters
    """
    request = DistanceCalculationRequest(
        from_station_id=from_station_id,
        to_station_id=to_station_id
    )

    service = DistanceCalculationService(db)
    result = await service.calculate_distance_and_time(request)

    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)

    return result