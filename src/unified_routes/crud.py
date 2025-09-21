from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, delete
from typing import List, Optional
from decimal import Decimal

from . import models, schemas

async def get_unified_routes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.UnifiedRoute]:
    stmt = select(models.UnifiedRoute).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_unified_route(db: AsyncSession, route_id: int) -> Optional[models.UnifiedRoute]:
    stmt = select(models.UnifiedRoute).where(models.UnifiedRoute.id == route_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_unified_route(db: AsyncSession, route: schemas.UnifiedRouteCreate) -> models.UnifiedRoute:
    # Calculate totals from segments
    total_distance = sum(segment.distance_km for segment in route.segments)
    total_duration = sum(segment.duration_minutes for segment in route.segments)

    # Create the route
    db_route = models.UnifiedRoute(
        name=route.name,
        description=route.description,
        line_id=route.line_id,
        status=route.status,
        total_distance=total_distance,
        total_duration=total_duration
    )

    db.add(db_route)
    await db.commit()
    await db.refresh(db_route)

    # Create segments
    for segment_data in route.segments:
        db_segment = models.RouteSegment(
            route_id=db_route.id,
            from_station_id=segment_data.from_station_id,
            to_station_id=segment_data.to_station_id,
            transport_type=segment_data.transport_type,
            distance_km=segment_data.distance_km,
            duration_minutes=segment_data.duration_minutes,
            order=segment_data.order
        )
        db.add(db_segment)

    await db.commit()
    await db.refresh(db_route)

    return db_route

async def update_unified_route(
    db: AsyncSession,
    route_id: int,
    route_update: schemas.UnifiedRouteUpdate
) -> Optional[models.UnifiedRoute]:
    db_route = await get_unified_route(db, route_id)
    if not db_route:
        return None

    # Update route basic info
    update_data = route_update.model_dump(exclude_unset=True, exclude={'segments'})
    for field, value in update_data.items():
        setattr(db_route, field, value)

    # Update segments if provided
    if route_update.segments is not None:
        # Delete existing segments
        delete_stmt = delete(models.RouteSegment).where(
            models.RouteSegment.route_id == route_id
        )
        await db.execute(delete_stmt)

        # Create new segments
        total_distance = Decimal('0')
        total_duration = 0

        for segment_data in route_update.segments:
            db_segment = models.RouteSegment(
                route_id=route_id,
                from_station_id=segment_data.from_station_id,
                to_station_id=segment_data.to_station_id,
                transport_type=segment_data.transport_type,
                distance_km=segment_data.distance_km,
                duration_minutes=segment_data.duration_minutes,
                order=segment_data.order
            )
            db.add(db_segment)
            total_distance += segment_data.distance_km
            total_duration += segment_data.duration_minutes

        # Update totals
        db_route.total_distance = total_distance
        db_route.total_duration = total_duration

    await db.commit()
    await db.refresh(db_route)

    return db_route

async def delete_unified_route(db: AsyncSession, route_id: int) -> bool:
    db_route = await get_unified_route(db, route_id)
    if not db_route:
        return False

    await db.delete(db_route)
    await db.commit()

    return True

async def get_route_segments(db: AsyncSession, route_id: int) -> List[models.RouteSegment]:
    stmt = select(models.RouteSegment).where(
        models.RouteSegment.route_id == route_id
    ).order_by(models.RouteSegment.order)
    result = await db.execute(stmt)
    return result.scalars().all()