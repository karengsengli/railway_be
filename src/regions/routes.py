from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from .service import RegionService
from .schemas import RegionCreate, RegionUpdate, RegionWithStats, RegionSearchResult

router = APIRouter(prefix="/regions", tags=["regions"])

@router.get("/", response_model=RegionSearchResult)
async def get_regions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all regions with statistics"""
    service = RegionService(db)
    return await service.get_regions(skip=skip, limit=limit, search=search)

@router.get("/{region_id}", response_model=RegionWithStats)
async def get_region(region_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific region by ID with statistics"""
    service = RegionService(db)
    region = await service.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region

@router.post("/", response_model=RegionWithStats, status_code=201)
async def create_region(region_data: RegionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new region"""
    service = RegionService(db)
    region = await service.create_region(region_data)
    await db.commit()

    # Return with stats
    return await service.get_region(region.id)

@router.put("/{region_id}", response_model=RegionWithStats)
async def update_region(
    region_id: int,
    region_data: RegionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a region"""
    service = RegionService(db)
    region = await service.update_region(region_id, region_data)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    await db.commit()

    # Return with stats
    return await service.get_region(region.id)

@router.delete("/{region_id}", status_code=204)
async def delete_region(region_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a region"""
    service = RegionService(db)
    try:
        success = await service.delete_region(region_id)
        if not success:
            raise HTTPException(status_code=404, detail="Region not found")

        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete region")