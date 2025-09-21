from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from decimal import Decimal

from ..models import TrainRoute, RouteSegment, TrainLine, Station
from .schemas import (
    TrainRouteCreate, TrainRouteUpdate,
    RouteSegmentCreate, RouteSegmentUpdate,
    RouteSegmentResponse, TrainRouteResponse
)

class RouteManagementService:
    """Service layer for route management operations"""

    @staticmethod
    async def create_train_route(db: AsyncSession, route_data: TrainRouteCreate) -> TrainRoute:
        """Create a new train route for a line"""

        # Check if line already has a route
        existing_route = await db.execute(
            select(TrainRoute).where(TrainRoute.line_id == route_data.line_id)
        )
        if existing_route.scalar_one_or_none():
            raise ValueError(f"Line {route_data.line_id} already has a route")

        # Verify line exists
        line = await db.execute(select(TrainLine).where(TrainLine.id == route_data.line_id))
        line = line.scalar_one_or_none()
        if not line:
            raise ValueError(f"Line {route_data.line_id} not found")

        train_route = TrainRoute(
            line_id=route_data.line_id,
            name=route_data.name,
            description=route_data.description
        )

        db.add(train_route)
        await db.commit()
        await db.refresh(train_route)
        return train_route

    @staticmethod
    async def get_train_route_by_line(db: AsyncSession, line_id: int) -> Optional[TrainRouteResponse]:
        """Get train route by line ID with segments"""

        result = await db.execute(
            select(TrainRoute)
            .options(selectinload(TrainRoute.route_segments))
            .where(TrainRoute.line_id == line_id)
        )
        train_route = result.scalar_one_or_none()

        if not train_route:
            return None

        # Get line info
        line_result = await db.execute(select(TrainLine).where(TrainLine.id == line_id))
        line = line_result.scalar_one_or_none()

        # Build response with segment details
        segments = []
        for segment in train_route.route_segments:
            # Get station names
            from_station_result = await db.execute(
                select(Station.name).where(Station.id == segment.from_station_id)
            )
            to_station_result = await db.execute(
                select(Station.name).where(Station.id == segment.to_station_id)
            )

            from_station_name = from_station_result.scalar_one_or_none()
            to_station_name = to_station_result.scalar_one_or_none()

            segment_response = RouteSegmentResponse(
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
            segments.append(segment_response)

        return TrainRouteResponse(
            id=train_route.id,
            line_id=train_route.line_id,
            name=train_route.name,
            description=train_route.description,
            total_distance_km=train_route.total_distance_km,
            total_duration_minutes=train_route.total_duration_minutes,
            status=train_route.status,
            created_at=train_route.created_at,
            updated_at=train_route.updated_at,
            line_name=line.name if line else None,
            line_color=line.color if line else None,
            route_segments=segments
        )

    @staticmethod
    async def add_route_segment(db: AsyncSession, train_route_id: int, segment_data: RouteSegmentCreate) -> RouteSegment:
        """Add a new route segment to the end of the route"""

        # Verify train route exists
        route_result = await db.execute(select(TrainRoute).where(TrainRoute.id == train_route_id))
        if not route_result.scalar_one_or_none():
            raise ValueError(f"Train route {train_route_id} not found")

        # Verify stations exist
        for station_id in [segment_data.from_station_id, segment_data.to_station_id]:
            station_result = await db.execute(select(Station).where(Station.id == station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"Station {station_id} not found")

        # Get next order number
        max_order_result = await db.execute(
            select(func.max(RouteSegment.segment_order))
            .where(RouteSegment.train_route_id == train_route_id)
        )
        max_order = max_order_result.scalar_one_or_none() or 0
        next_order = max_order + 1

        segment = RouteSegment(
            train_route_id=train_route_id,
            from_station_id=segment_data.from_station_id,
            to_station_id=segment_data.to_station_id,
            segment_order=next_order,
            distance_km=segment_data.distance_km,
            duration_minutes=segment_data.duration_minutes,
            transport_type=segment_data.transport_type
        )

        db.add(segment)
        await db.commit()
        await db.refresh(segment)

        # Update route totals
        await RouteManagementService._update_route_totals(db, train_route_id)

        return segment

    @staticmethod
    async def move_segment(db: AsyncSession, segment_id: int, direction: str) -> bool:
        """Move a segment up or down in the order"""

        # Get the segment
        segment_result = await db.execute(select(RouteSegment).where(RouteSegment.id == segment_id))
        segment = segment_result.scalar_one_or_none()
        if not segment:
            raise ValueError(f"Segment {segment_id} not found")

        current_order = segment.segment_order
        train_route_id = segment.train_route_id

        if direction == "up":
            new_order = current_order - 1
            if new_order < 1:
                return False  # Already at top
        else:  # down
            # Check if there's a segment below
            max_order_result = await db.execute(
                select(func.max(RouteSegment.segment_order))
                .where(RouteSegment.train_route_id == train_route_id)
            )
            max_order = max_order_result.scalar_one_or_none() or 0
            new_order = current_order + 1
            if new_order > max_order:
                return False  # Already at bottom

        # Find the segment to swap with
        swap_segment_result = await db.execute(
            select(RouteSegment).where(
                RouteSegment.train_route_id == train_route_id,
                RouteSegment.segment_order == new_order
            )
        )
        swap_segment = swap_segment_result.scalar_one_or_none()

        if swap_segment:
            # Get max order to use as temporary value (constraint requires > 0)
            max_order_result = await db.execute(
                select(func.max(RouteSegment.segment_order))
                .where(RouteSegment.train_route_id == train_route_id)
            )
            max_order = max_order_result.scalar_one_or_none() or 0
            temp_order = max_order + 1000  # Use a high temporary value

            # Step 1: Move first segment to temporary order
            await db.execute(
                update(RouteSegment)
                .where(RouteSegment.id == segment.id)
                .values(segment_order=temp_order)
            )
            await db.flush()

            # Step 2: Move swap segment to current segment's order
            await db.execute(
                update(RouteSegment)
                .where(RouteSegment.id == swap_segment.id)
                .values(segment_order=current_order)
            )
            await db.flush()

            # Step 3: Move first segment to final order
            await db.execute(
                update(RouteSegment)
                .where(RouteSegment.id == segment.id)
                .values(segment_order=new_order)
            )

            await db.commit()
            return True

        return False

    @staticmethod
    async def update_route_segment(db: AsyncSession, segment_id: int, segment_data: RouteSegmentUpdate) -> Optional[RouteSegment]:
        """Update an existing route segment"""

        # Get the segment to update
        segment_result = await db.execute(select(RouteSegment).where(RouteSegment.id == segment_id))
        segment = segment_result.scalar_one_or_none()
        if not segment:
            return None

        # Store the train_route_id for later use
        train_route_id = segment.train_route_id

        # Verify stations exist if they're being updated
        if segment_data.from_station_id:
            station_result = await db.execute(select(Station).where(Station.id == segment_data.from_station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"From station {segment_data.from_station_id} not found")

        if segment_data.to_station_id:
            station_result = await db.execute(select(Station).where(Station.id == segment_data.to_station_id))
            if not station_result.scalar_one_or_none():
                raise ValueError(f"To station {segment_data.to_station_id} not found")

        # Validate that from and to stations are different
        from_station_id = segment_data.from_station_id or segment.from_station_id
        to_station_id = segment_data.to_station_id or segment.to_station_id
        if from_station_id == to_station_id:
            raise ValueError("From and to stations must be different")

        # Update the segment fields
        update_data = {}
        if segment_data.from_station_id is not None:
            update_data["from_station_id"] = segment_data.from_station_id
        if segment_data.to_station_id is not None:
            update_data["to_station_id"] = segment_data.to_station_id
        if segment_data.distance_km is not None:
            update_data["distance_km"] = segment_data.distance_km
        if segment_data.duration_minutes is not None:
            update_data["duration_minutes"] = segment_data.duration_minutes
        if segment_data.transport_type is not None:
            update_data["transport_type"] = segment_data.transport_type

        if update_data:
            await db.execute(
                update(RouteSegment)
                .where(RouteSegment.id == segment_id)
                .values(**update_data)
            )
            await db.commit()

            # Update route totals if distance or duration changed
            if "distance_km" in update_data or "duration_minutes" in update_data:
                await RouteManagementService._update_route_totals(db, train_route_id)

            # Refresh and return updated segment
            await db.refresh(segment)

        return segment

    @staticmethod
    async def delete_segment(db: AsyncSession, segment_id: int) -> bool:
        """Delete a route segment and reorder remaining segments"""

        # Get the segment to delete
        segment_result = await db.execute(select(RouteSegment).where(RouteSegment.id == segment_id))
        segment = segment_result.scalar_one_or_none()
        if not segment:
            return False

        deleted_order = segment.segment_order
        train_route_id = segment.train_route_id

        # Delete the segment
        await db.execute(delete(RouteSegment).where(RouteSegment.id == segment_id))

        # Reorder remaining segments (move up all segments after the deleted one)
        await db.execute(
            update(RouteSegment)
            .where(
                RouteSegment.train_route_id == train_route_id,
                RouteSegment.segment_order > deleted_order
            )
            .values(segment_order=RouteSegment.segment_order - 1)
        )

        await db.commit()

        # Update route totals
        await RouteManagementService._update_route_totals(db, train_route_id)

        return True

    @staticmethod
    async def _update_route_totals(db: AsyncSession, train_route_id: int):
        """Update the total distance and duration for a route"""

        # Calculate totals
        totals_result = await db.execute(
            select(
                func.sum(RouteSegment.distance_km).label('total_distance'),
                func.sum(RouteSegment.duration_minutes).label('total_duration')
            )
            .where(RouteSegment.train_route_id == train_route_id)
        )
        totals = totals_result.first()

        # Update the route
        await db.execute(
            update(TrainRoute)
            .where(TrainRoute.id == train_route_id)
            .values(
                total_distance_km=totals.total_distance or Decimal('0'),
                total_duration_minutes=totals.total_duration or 0
            )
        )
        await db.commit()

    @staticmethod
    async def get_all_train_routes(db: AsyncSession) -> List[TrainRouteResponse]:
        """Get all train routes"""

        result = await db.execute(
            select(TrainRoute)
            .options(selectinload(TrainRoute.line))
            .order_by(TrainRoute.name)
        )
        routes = result.scalars().all()

        response_routes = []
        for route in routes:
            response_routes.append(TrainRouteResponse(
                id=route.id,
                line_id=route.line_id,
                name=route.name,
                description=route.description,
                total_distance_km=route.total_distance_km,
                total_duration_minutes=route.total_duration_minutes,
                status=route.status,
                created_at=route.created_at,
                updated_at=route.updated_at,
                line_name=route.line.name if route.line else None,
                line_color=route.line.color if route.line else None,
                route_segments=[]
            ))

        return response_routes