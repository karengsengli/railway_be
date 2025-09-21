from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from decimal import Decimal

from ..models import IntersectionPoint, IntersectionSegment, Station, TrainLine
from .schemas import (
    IntersectionPointCreate, IntersectionPointUpdate, IntersectionPointResponse,
    IntersectionSegmentCreate, IntersectionSegmentUpdate, IntersectionSegmentResponse,
    IntersectionPointWithSegmentsResponse
)

class IntersectionManagementService:
    """Service layer for intersection management operations"""

    # Intersection Point Operations
    @staticmethod
    async def create_intersection_point(db: AsyncSession, point_data: IntersectionPointCreate) -> IntersectionPoint:
        """Create a new intersection point"""

        intersection_point = IntersectionPoint(
            name=point_data.name,
            description=point_data.description,
            lat=point_data.lat,
            long=point_data.long,
            station_codes=point_data.station_codes,
            accessibility_features=point_data.accessibility_features
        )

        db.add(intersection_point)
        await db.commit()
        await db.refresh(intersection_point)
        return intersection_point

    @staticmethod
    async def get_all_intersection_points(db: AsyncSession) -> List[IntersectionPointResponse]:
        """Get all intersection points"""

        result = await db.execute(
            select(IntersectionPoint)
            .where(IntersectionPoint.status == "active")
            .order_by(IntersectionPoint.name)
        )
        points = result.scalars().all()

        return [
            IntersectionPointResponse(
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
            ) for point in points
        ]

    @staticmethod
    async def get_intersection_point_with_segments(db: AsyncSession, point_id: int) -> Optional[IntersectionPointWithSegmentsResponse]:
        """Get intersection point with all its segments"""

        result = await db.execute(
            select(IntersectionPoint)
            .options(selectinload(IntersectionPoint.intersection_segments))
            .where(IntersectionPoint.id == point_id)
        )
        point = result.scalar_one_or_none()

        if not point:
            return None

        # Build segments with additional details
        segments = []
        for segment in point.intersection_segments:
            # Get station and line names
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

            from_station_name = from_station_result.scalar_one_or_none()
            to_station_name = to_station_result.scalar_one_or_none()
            from_line_data = from_line_result.first()
            to_line_data = to_line_result.first()

            segment_response = IntersectionSegmentResponse(
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
                intersection_point_name=point.name
            )
            segments.append(segment_response)

        return IntersectionPointWithSegmentsResponse(
            id=point.id,
            name=point.name,
            description=point.description,
            lat=point.lat,
            long=point.long,
            station_codes=point.station_codes,
            accessibility_features=point.accessibility_features,
            status=point.status,
            created_at=point.created_at,
            updated_at=point.updated_at,
            intersection_segments=segments
        )

    @staticmethod
    async def update_intersection_point(db: AsyncSession, point_id: int, point_data: IntersectionPointUpdate) -> Optional[IntersectionPoint]:
        """Update an intersection point"""

        point_result = await db.execute(select(IntersectionPoint).where(IntersectionPoint.id == point_id))
        point = point_result.scalar_one_or_none()
        if not point:
            return None

        update_data = {}
        if point_data.name is not None:
            update_data["name"] = point_data.name
        if point_data.description is not None:
            update_data["description"] = point_data.description
        if point_data.lat is not None:
            update_data["lat"] = point_data.lat
        if point_data.long is not None:
            update_data["long"] = point_data.long
        if point_data.station_codes is not None:
            update_data["station_codes"] = point_data.station_codes
        if point_data.accessibility_features is not None:
            update_data["accessibility_features"] = point_data.accessibility_features

        if update_data:
            await db.execute(
                update(IntersectionPoint)
                .where(IntersectionPoint.id == point_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(point)

        return point

    @staticmethod
    async def delete_intersection_point(db: AsyncSession, point_id: int) -> bool:
        """Delete an intersection point and all its segments"""

        point_result = await db.execute(select(IntersectionPoint).where(IntersectionPoint.id == point_id))
        point = point_result.scalar_one_or_none()
        if not point:
            return False

        # Delete all segments first
        await db.execute(delete(IntersectionSegment).where(IntersectionSegment.intersection_point_id == point_id))

        # Delete the point
        await db.execute(delete(IntersectionPoint).where(IntersectionPoint.id == point_id))
        await db.commit()
        return True

    # Intersection Segment Operations
    @staticmethod
    async def create_intersection_segment(db: AsyncSession, segment_data: IntersectionSegmentCreate) -> IntersectionSegment:
        """Create a new intersection segment"""

        # Verify intersection point exists
        point_result = await db.execute(select(IntersectionPoint).where(IntersectionPoint.id == segment_data.intersection_point_id))
        if not point_result.scalar_one_or_none():
            raise ValueError(f"Intersection point {segment_data.intersection_point_id} not found")

        # Verify stations exist
        for station_id in [segment_data.from_station_id, segment_data.to_station_id]:
            station_result = await db.execute(select(Station).where(Station.id == station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"Station {station_id} not found")

        # Verify lines exist
        for line_id in [segment_data.from_line_id, segment_data.to_line_id]:
            line_result = await db.execute(select(TrainLine).where(TrainLine.id == line_id))
            if not line_result.scalar_one_or_none():
                raise ValueError(f"Train line {line_id} not found")

        segment = IntersectionSegment(
            intersection_point_id=segment_data.intersection_point_id,
            from_station_id=segment_data.from_station_id,
            to_station_id=segment_data.to_station_id,
            from_line_id=segment_data.from_line_id,
            to_line_id=segment_data.to_line_id,
            distance_km=segment_data.distance_km,
            duration_minutes=segment_data.duration_minutes,
            transport_type=segment_data.transport_type,
            transfer_cost=segment_data.transfer_cost,
            direction_instructions=segment_data.direction_instructions,
            accessibility_notes=segment_data.accessibility_notes
        )

        db.add(segment)
        await db.commit()
        await db.refresh(segment)
        return segment

    @staticmethod
    async def get_all_intersection_segments(db: AsyncSession) -> List[IntersectionSegmentResponse]:
        """Get all intersection segments with details"""

        result = await db.execute(
            select(IntersectionSegment)
            .where(IntersectionSegment.status == "active")
            .order_by(IntersectionSegment.intersection_point_id, IntersectionSegment.id)
        )
        segments = result.scalars().all()

        response_segments = []
        for segment in segments:
            # Get additional details
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

            segment_response = IntersectionSegmentResponse(
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
            response_segments.append(segment_response)

        return response_segments

    @staticmethod
    async def update_intersection_segment(db: AsyncSession, segment_id: int, segment_data: IntersectionSegmentUpdate) -> Optional[IntersectionSegment]:
        """Update an intersection segment"""

        segment_result = await db.execute(select(IntersectionSegment).where(IntersectionSegment.id == segment_id))
        segment = segment_result.scalar_one_or_none()
        if not segment:
            return None

        # Verify foreign keys if they're being updated
        if segment_data.intersection_point_id:
            point_result = await db.execute(select(IntersectionPoint).where(IntersectionPoint.id == segment_data.intersection_point_id))
            if not point_result.scalar_one_or_none():
                raise ValueError(f"Intersection point {segment_data.intersection_point_id} not found")

        if segment_data.from_station_id:
            station_result = await db.execute(select(Station).where(Station.id == segment_data.from_station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"From station {segment_data.from_station_id} not found")

        if segment_data.to_station_id:
            station_result = await db.execute(select(Station).where(Station.id == segment_data.to_station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"To station {segment_data.to_station_id} not found")

        if segment_data.from_line_id:
            line_result = await db.execute(select(TrainLine).where(TrainLine.id == segment_data.from_line_id))
            if not line_result.scalar_one_or_none():
                raise ValueError(f"From line {segment_data.from_line_id} not found")

        if segment_data.to_line_id:
            line_result = await db.execute(select(TrainLine).where(TrainLine.id == segment_data.to_line_id))
            if not line_result.scalar_one_or_none():
                raise ValueError(f"To line {segment_data.to_line_id} not found")

        # Build update data
        update_data = {}
        for field, value in segment_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if update_data:
            await db.execute(
                update(IntersectionSegment)
                .where(IntersectionSegment.id == segment_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(segment)

        return segment

    @staticmethod
    async def delete_intersection_segment(db: AsyncSession, segment_id: int) -> bool:
        """Delete an intersection segment"""

        segment_result = await db.execute(select(IntersectionSegment).where(IntersectionSegment.id == segment_id))
        segment = segment_result.scalar_one_or_none()
        if not segment:
            return False

        await db.execute(delete(IntersectionSegment).where(IntersectionSegment.id == segment_id))
        await db.commit()
        return True