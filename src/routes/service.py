from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import Route
from .schemas import RouteWithDetails, RouteCreate
from ..models import Station, TrainLine

class RouteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_routes(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[int] = None
    ) -> List[RouteWithDetails]:

        query = select(Route).options(
            selectinload(Route.line),
            selectinload(Route.from_station),
            selectinload(Route.to_station)
        )

        if line_id:
            query = query.where(Route.line_id == line_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        routes = result.scalars().all()

        routes_with_details = []
        for route in routes:
            route_data = RouteWithDetails(
                id=route.id,
                line_id=route.line_id,
                from_station_id=route.from_station_id,
                to_station_id=route.to_station_id,
                transport_type=route.transport_type,
                distance_km=route.distance_km,
                duration_minutes=route.duration_minutes,
                station_count=route.station_count,
                status=route.status,
                created_at=route.created_at,
                updated_at=route.updated_at,
                line_name=route.line.name if route.line else None,
                from_station_name=route.from_station.name if route.from_station else None,
                to_station_name=route.to_station.name if route.to_station else None
            )
            routes_with_details.append(route_data)

        return routes_with_details

    async def get_route(self, route_id: int) -> Optional[RouteWithDetails]:
        query = select(Route).options(
            selectinload(Route.line),
            selectinload(Route.from_station),
            selectinload(Route.to_station)
        ).where(Route.id == route_id)

        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return None

        return RouteWithDetails(
            id=route.id,
            line_id=route.line_id,
            from_station_id=route.from_station_id,
            to_station_id=route.to_station_id,
            transport_type=route.transport_type,
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
            station_count=route.station_count,
            status=route.status,
            created_at=route.created_at,
            updated_at=route.updated_at,
            line_name=route.line.name if route.line else None,
            from_station_name=route.from_station.name if route.from_station else None,
            to_station_name=route.to_station.name if route.to_station else None
        )

    async def create_route(self, route_data: RouteCreate) -> RouteWithDetails:
        # Create new route
        new_route = Route(**route_data.model_dump())
        self.db.add(new_route)
        await self.db.commit()
        await self.db.refresh(new_route)

        # Return the created route with details
        return await self.get_route(new_route.id)

    async def update_route(self, route_id: int, route_data: RouteCreate) -> Optional[RouteWithDetails]:
        query = select(Route).where(Route.id == route_id)
        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return None

        # Update route fields
        for field, value in route_data.model_dump(exclude_unset=True).items():
            setattr(route, field, value)

        await self.db.commit()
        await self.db.refresh(route)

        return await self.get_route(route_id)

    async def delete_route(self, route_id: int) -> bool:
        query = select(Route).where(Route.id == route_id)
        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return False

        await self.db.delete(route)
        await self.db.commit()
        return True