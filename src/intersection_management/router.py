from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from ..database import get_db
from .service import IntersectionManagementService
from .schemas import (
    IntersectionPointCreate, IntersectionPointUpdate, IntersectionPointResponse,
    IntersectionSegmentCreate, IntersectionSegmentUpdate, IntersectionSegmentResponse,
    IntersectionOperationResponse, IntersectionPointWithSegmentsResponse
)

router = APIRouter(prefix="/intersection-management", tags=["Intersection Management"])

# Intersection Point Endpoints
@router.post("/points/", response_model=IntersectionPointResponse)
async def create_intersection_point(
    point_data: IntersectionPointCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new intersection point"""
    try:
        point = await IntersectionManagementService.create_intersection_point(db, point_data)
        return IntersectionPointResponse(
            id=point.id,
            name=point.name,
            description=point.description,
            lat=point.lat,
            long=point.long,
            station_codes=point.station_codes,
            accessibility_features=point.accessibility_features,
            status=point.status,
            created_at=point.created_at,
            updated_at=point.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.get("/points/", response_model=List[IntersectionPointResponse])
async def get_all_intersection_points(db: AsyncSession = Depends(get_db)):
    """Get all intersection points"""
    return await IntersectionManagementService.get_all_intersection_points(db)

@router.get("/points/{point_id}", response_model=IntersectionPointWithSegmentsResponse)
async def get_intersection_point_with_segments(
    point_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get intersection point with all its segments"""
    point = await IntersectionManagementService.get_intersection_point_with_segments(db, point_id)
    if not point:
        raise HTTPException(status_code=404, detail="Intersection point not found")
    return point

@router.put("/points/{point_id}", response_model=IntersectionPointResponse)
async def update_intersection_point(
    point_id: int,
    point_data: IntersectionPointUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an intersection point"""
    try:
        point = await IntersectionManagementService.update_intersection_point(db, point_id, point_data)
        if not point:
            raise HTTPException(status_code=404, detail="Intersection point not found")

        return IntersectionPointResponse(
            id=point.id,
            name=point.name,
            description=point.description,
            lat=point.lat,
            long=point.long,
            station_codes=point.station_codes,
            accessibility_features=point.accessibility_features,
            status=point.status,
            created_at=point.created_at,
            updated_at=point.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/points/{point_id}", response_model=IntersectionOperationResponse)
async def delete_intersection_point(
    point_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an intersection point and all its segments"""
    success = await IntersectionManagementService.delete_intersection_point(db, point_id)
    if success:
        return IntersectionOperationResponse(
            success=True,
            message="Intersection point deleted successfully"
        )
    else:
        raise HTTPException(status_code=404, detail="Intersection point not found")

# Intersection Segment Endpoints
@router.post("/segments/", response_model=IntersectionSegmentResponse)
async def create_intersection_segment(
    segment_data: IntersectionSegmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new intersection segment"""
    try:
        segment = await IntersectionManagementService.create_intersection_segment(db, segment_data)

        # Get additional details for response
        from ..models import Station, TrainLine, IntersectionPoint
        from sqlalchemy import select

        from_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.from_station_id)
        )
        to_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.to_station_id)
        )
        from_line_result = await db.execute(
            select(TrainLine.name, TrainLine.color).where(TrainLine.id == segment.from_line_id)
        )
        to_line_result = await db.execute(
            select(TrainLine.name, TrainLine.color).where(TrainLine.id == segment.to_line_id)
        )
        point_result = await db.execute(
            select(IntersectionPoint.name).where(IntersectionPoint.id == segment.intersection_point_id)
        )

        from_station_name = from_station_result.scalar_one_or_none()
        to_station_name = to_station_result.scalar_one_or_none()
        from_line_data = from_line_result.first()
        to_line_data = to_line_result.first()
        point_name = point_result.scalar_one_or_none()

        return IntersectionSegmentResponse(
            id=segment.id,
            intersection_point_id=segment.intersection_point_id,
            from_station_id=segment.from_station_id,
            to_station_id=segment.to_station_id,
            from_line_id=segment.from_line_id,
            to_line_id=segment.to_line_id,
            distance_km=segment.distance_km,
            duration_minutes=segment.duration_minutes,
            transport_type=segment.transport_type,
            transfer_cost=segment.transfer_cost,
            direction_instructions=segment.direction_instructions,
            accessibility_notes=segment.accessibility_notes,
            status=segment.status,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
            from_station_name=from_station_name,
            to_station_name=to_station_name,
            from_line_name=from_line_data.name if from_line_data else None,
            to_line_name=to_line_data.name if to_line_data else None,
            from_line_color=from_line_data.color if from_line_data else None,
            to_line_color=to_line_data.color if to_line_data else None,
            intersection_point_name=point_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(status_code=400, detail="This intersection segment already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.get("/segments/", response_model=List[IntersectionSegmentResponse])
async def get_all_intersection_segments(db: AsyncSession = Depends(get_db)):
    """Get all intersection segments with details"""
    return await IntersectionManagementService.get_all_intersection_segments(db)

@router.put("/segments/{segment_id}", response_model=IntersectionSegmentResponse)
async def update_intersection_segment(
    segment_id: int,
    segment_data: IntersectionSegmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an intersection segment"""
    try:
        segment = await IntersectionManagementService.update_intersection_segment(db, segment_id, segment_data)
        if not segment:
            raise HTTPException(status_code=404, detail="Intersection segment not found")

        # Get additional details for response
        from ..models import Station, TrainLine, IntersectionPoint
        from sqlalchemy import select

        from_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.from_station_id)
        )
        to_station_result = await db.execute(
            select(Station.name).where(Station.id == segment.to_station_id)
        )
        from_line_result = await db.execute(
            select(TrainLine.name, TrainLine.color).where(TrainLine.id == segment.from_line_id)
        )
        to_line_result = await db.execute(
            select(TrainLine.name, TrainLine.color).where(TrainLine.id == segment.to_line_id)
        )
        point_result = await db.execute(
            select(IntersectionPoint.name).where(IntersectionPoint.id == segment.intersection_point_id)
        )

        from_station_name = from_station_result.scalar_one_or_none()
        to_station_name = to_station_result.scalar_one_or_none()
        from_line_data = from_line_result.first()
        to_line_data = to_line_result.first()
        point_name = point_result.scalar_one_or_none()

        return IntersectionSegmentResponse(
            id=segment.id,
            intersection_point_id=segment.intersection_point_id,
            from_station_id=segment.from_station_id,
            to_station_id=segment.to_station_id,
            from_line_id=segment.from_line_id,
            to_line_id=segment.to_line_id,
            distance_km=segment.distance_km,
            duration_minutes=segment.duration_minutes,
            transport_type=segment.transport_type,
            transfer_cost=segment.transfer_cost,
            direction_instructions=segment.direction_instructions,
            accessibility_notes=segment.accessibility_notes,
            status=segment.status,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
            from_station_name=from_station_name,
            to_station_name=to_station_name,
            from_line_name=from_line_data.name if from_line_data else None,
            to_line_name=to_line_data.name if to_line_data else None,
            from_line_color=from_line_data.color if from_line_data else None,
            to_line_color=to_line_data.color if to_line_data else None,
            intersection_point_name=point_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(status_code=400, detail="This intersection segment configuration already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")

@router.delete("/segments/{segment_id}", response_model=IntersectionOperationResponse)
async def delete_intersection_segment(
    segment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an intersection segment"""
    success = await IntersectionManagementService.delete_intersection_segment(db, segment_id)
    if success:
        return IntersectionOperationResponse(
            success=True,
            message="Intersection segment deleted successfully"
        )
    else:
        raise HTTPException(status_code=404, detail="Intersection segment not found")

# Convenience endpoints
@router.get("/points/{point_id}/segments/", response_model=List[IntersectionSegmentResponse])
async def get_segments_for_intersection_point(
    point_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all segments for a specific intersection point"""
    point_with_segments = await IntersectionManagementService.get_intersection_point_with_segments(db, point_id)
    if not point_with_segments:
        raise HTTPException(status_code=404, detail="Intersection point not found")
    return point_with_segments.intersection_segments