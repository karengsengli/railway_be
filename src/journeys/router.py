from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from ..auth.dependencies import get_current_user
from .service import JourneyService
from .schemas import JourneyCreate, JourneyWithDetails, Journey

router = APIRouter()

@router.post("/", response_model=Journey)
async def create_journey(
    journey: JourneyCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JourneyService(db)
    return await service.create_journey(journey, current_user.id)

@router.get("/", response_model=List[JourneyWithDetails])
async def get_journeys(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JourneyService(db)
    return await service.get_journeys(current_user.id, skip, limit)

@router.get("/{journey_id}", response_model=JourneyWithDetails)
async def get_journey(
    journey_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JourneyService(db)
    journey = await service.get_journey(journey_id)

    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    # Check if user owns the journey or is admin
    if journey.user_id != current_user.id:
        # TODO: Add admin role check here
        raise HTTPException(status_code=403, detail="Not authorized to view this journey")

    return journey

@router.put("/{journey_id}", response_model=JourneyWithDetails)
async def update_journey(
    journey_id: int,
    journey: JourneyCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JourneyService(db)
    existing_journey = await service.get_journey(journey_id)

    if not existing_journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    # Check if user owns the journey or is admin
    if existing_journey.user_id != current_user.id:
        # TODO: Add admin role check here
        raise HTTPException(status_code=403, detail="Not authorized to update this journey")

    updated_journey = await service.update_journey(journey_id, journey)
    if not updated_journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    return updated_journey

@router.delete("/{journey_id}", status_code=204)
async def delete_journey(
    journey_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JourneyService(db)
    existing_journey = await service.get_journey(journey_id)

    if not existing_journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    # Check if user owns the journey or is admin
    if existing_journey.user_id != current_user.id:
        # TODO: Add admin role check here
        raise HTTPException(status_code=403, detail="Not authorized to delete this journey")

    success = await service.delete_journey(journey_id)
    if not success:
        raise HTTPException(status_code=404, detail="Journey not found")