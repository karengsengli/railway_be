from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List

from ..database import get_db
from ..models import TrainRoute
from .service import RouteManagementService
from .schemas import (
    TrainRouteCreate, TrainRouteUpdate, TrainRouteResponse,
    RouteSegmentCreate, RouteSegmentUpdate, RouteSegmentResponse,
    RouteSegmentMoveRequest, RouteOperationResponse
)

router = APIRouter(prefix="/route-management", tags=["Route Management"])

# Train Route Endpoints
@router.post("/routes/", response_model=TrainRouteResponse)
async def create_train_route(
    route_data: TrainRouteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new train route for a line"""
    try:
        route = await RouteManagementService.create_train_route(db, route_data)
        return await RouteManagementService.get_train_route_by_line(db, route.line_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/routes/", response_model=List[TrainRouteResponse])
async def get_all_train_routes(db: AsyncSession = Depends(get_db)):
    """Get all train routes"""
    return await RouteManagementService.get_all_train_routes(db)

@router.get("/routes/line/{line_id}", response_model=TrainRouteResponse)
async def get_train_route_by_line(line_id: int, db: AsyncSession = Depends(get_db)):
    """Get train route by line ID with segments"""
    route = await RouteManagementService.get_train_route_by_line(db, line_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found for this line")
    return route

# Route Segment Endpoints
@router.post("/routes/{route_id}/segments/", response_model=RouteSegmentResponse)
async def add_route_segment(
    route_id: int,
    segment_data: RouteSegmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new route segment to the end of the route"""
    try:
        segment = await RouteManagementService.add_route_segment(db, route_id, segment_data)

        # Return basic segment response to avoid complexity
        return RouteSegmentResponse(
            id=segment.id,
            train_route_id=segment.train_route_id,
            from_station_id=segment.from_station_id,
            to_station_id=segment.to_station_id,
            segment_order=segment.segment_order,
            distance_km=segment.distance_km,
            duration_minutes=segment.duration_minutes,
            transport_type=segment.transport_type,
            status=segment.status,
            created_at=segment.created_at,
            updated_at=segment.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(status_code=400, detail="This route segment already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.put("/segments/{segment_id}", response_model=RouteSegmentResponse)
async def update_route_segment(
    segment_id: int,
    segment_data: RouteSegmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing route segment"""
    try:
        segment = await RouteManagementService.update_route_segment(db, segment_id, segment_data)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        # Get station names for response
        from ..models import Station
        from_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.from_station_id)
        )
        to_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.to_station_id)
        )

        from_station_name = from_station_result.scalar_one_or_none()
        to_station_name = to_station_result.scalar_one_or_none()

        return RouteSegmentResponse(
            id=segment.id,
            train_route_id=segment.train_route_id,
            from_station_id=segment.from_station_id,
            to_station_id=segment.to_station_id,
            segment_order=segment.segment_order,
            distance_km=segment.distance_km,
            duration_minutes=segment.duration_minutes,
            transport_type=segment.transport_type,
            status=segment.status,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
            from_station_name=from_station_name,
            to_station_name=to_station_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(status_code=400, detail="This route segment configuration already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.put("/segments/{segment_id}/move", response_model=RouteOperationResponse)
async def move_segment(
    segment_id: int,
    move_request: RouteSegmentMoveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Move a segment up or down in the order"""
    try:
        success = await RouteManagementService.move_segment(db, segment_id, move_request.direction)
        if success:
            return RouteOperationResponse(
                success=True,
                message=f"Segment moved {move_request.direction} successfully"
            )
        else:
            return RouteOperationResponse(
                success=False,
                message=f"Cannot move segment {move_request.direction} - already at limit"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/segments/{segment_id}", response_model=RouteOperationResponse)
async def delete_segment(segment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a route segment and reorder remaining segments"""
    success = await RouteManagementService.delete_segment(db, segment_id)
    if success:
        return RouteOperationResponse(
            success=True,
            message="Segment deleted successfully"
        )
    else:
        raise HTTPException(status_code=404, detail="Segment not found")

# Convenience endpoints
@router.get("/lines/{line_id}/route-with-segments", response_model=TrainRouteResponse)
async def get_line_route_with_segments(line_id: int, db: AsyncSession = Depends(get_db)):
    """Get complete route information for a line including all segments"""
    route = await RouteManagementService.get_train_route_by_line(db, line_id)
    if not route:
        raise HTTPException(status_code=404, detail="No route found for this line")
    return route

@router.post("/lines/{line_id}/create-route-with-segments")
async def create_route_with_segments(
    line_id: int,
    route_data: TrainRouteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a route and return it with segments for immediate use"""
    try:
        # Ensure line_id matches
        route_data.line_id = line_id

        route = await RouteManagementService.create_train_route(db, route_data)
        return await RouteManagementService.get_train_route_by_line(db, route.line_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))