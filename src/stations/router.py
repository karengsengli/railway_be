from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from .service import StationService
from .schemas import StationWithLine, StationSearchResult, StationCreate, Station

router = APIRouter()

@router.get("/", response_model=StationSearchResult)
async def get_stations(
    skip: int = 0,
    limit: int = 100,
    line_id: Optional[int] = None,
    region_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    return await service.get_stations(
        skip=skip,
        limit=limit,
        line_id=line_id,
        region_id=region_id,
        search=search
    )

@router.get("/search", response_model=List[StationWithLine])
async def search_stations(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    return await service.search_stations(q, limit)

@router.get("/line/{line_id}", response_model=List[StationWithLine])
async def get_stations_by_line(
    line_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    return await service.get_stations_by_line(line_id)

@router.post("/", response_model=StationWithLine, status_code=201)
async def create_station(
    station_data: StationCreate,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    try:
        station = await service.create_station(station_data)
        await db.commit()
        return await service.get_station(station.id)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{station_id}", response_model=StationWithLine)
async def update_station(
    station_id: int,
    station_data: StationCreate,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    try:
        station = await service.update_station(station_id, station_data)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
        await db.commit()
        return await service.get_station(station.id)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{station_id}", status_code=204)
async def delete_station(
    station_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    try:
        success = await service.delete_station(station_id)
        if not success:
            raise HTTPException(status_code=404, detail="Station not found")
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{station_id}", response_model=StationWithLine)
async def get_station(
    station_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = StationService(db)
    station = await service.get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station