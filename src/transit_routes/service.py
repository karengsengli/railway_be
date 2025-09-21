from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import TransitRoute, RouteStop, Station
from .schemas import TransitRouteCreate, TransitRouteWithDetails, RouteStopWithDetails

class TransitRouteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_transit_routes(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        query = select(TransitRoute).options(
            selectinload(TransitRoute.route_stops).selectinload(RouteStop.station)
        )

        query = query.offset(skip).limit(limit).order_by(TransitRoute.created_at.desc())
        result = await self.db.execute(query)
        routes = result.scalars().all()

        routes_with_details = []
        for route in routes:
            stops_with_details = []
            for stop in sorted(route.route_stops, key=lambda x: x.stop_order):
                # Get station lines information
                station_lines = []
                if stop.station and hasattr(stop.station, 'lines'):
                    station_lines = []

                stop_detail = RouteStopWithDetails(
                    id=stop.id,
                    transit_route_id=stop.transit_route_id,
                    station_id=stop.station_id,
                    stop_order=stop.stop_order,
                    order=stop.stop_order,
                    created_at=stop.created_at,
                    updated_at=stop.updated_at,
                    station_name=stop.station.name if stop.station else None,
                    lines=station_lines
                )
                stops_with_details.append(stop_detail)

            route_data = TransitRouteWithDetails(
                id=route.id,
                name=route.name,
                description=route.description,
                status=route.status,
                total_stations=route.total_stations,
                estimated_time=route.estimated_time,
                created_at=route.created_at,
                updated_at=route.updated_at,
                stops=stops_with_details
            )
            routes_with_details.append(route_data)

        return {
            "routes": routes_with_details,
            "total_count": len(routes_with_details)
        }

    async def get_transit_route(self, route_id: int) -> Optional[TransitRouteWithDetails]:
        query = select(TransitRoute).options(
            selectinload(TransitRoute.route_stops).selectinload(RouteStop.station)
        ).where(TransitRoute.id == route_id)

        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return None

        stops_with_details = []
        for stop in sorted(route.route_stops, key=lambda x: x.stop_order):
            station_lines = []

            stop_detail = RouteStopWithDetails(
                id=stop.id,
                transit_route_id=stop.transit_route_id,
                station_id=stop.station_id,
                stop_order=stop.stop_order,
                order=stop.stop_order,
                created_at=stop.created_at,
                updated_at=stop.updated_at,
                station_name=stop.station.name if stop.station else None,
                lines=station_lines
            )
            stops_with_details.append(stop_detail)

        return TransitRouteWithDetails(
            id=route.id,
            name=route.name,
            description=route.description,
            status=route.status,
            total_stations=route.total_stations,
            estimated_time=route.estimated_time,
            created_at=route.created_at,
            updated_at=route.updated_at,
            stops=stops_with_details
        )

    async def create_transit_route(self, route_data: TransitRouteCreate) -> TransitRouteWithDetails:
        # Create new transit route
        new_route = TransitRoute(
            name=route_data.name,
            description=route_data.description,
            status=route_data.status,
            total_stations=len(route_data.stops),
            estimated_time=route_data.estimated_time
        )
        self.db.add(new_route)
        await self.db.commit()
        await self.db.refresh(new_route)

        # Create route stops
        for stop in route_data.stops:
            route_stop = RouteStop(
                transit_route_id=new_route.id,
                station_id=stop.station_id,
                stop_order=stop.stop_order
            )
            self.db.add(route_stop)

        await self.db.commit()

        return await self.get_transit_route(new_route.id)

    async def update_transit_route(self, route_id: int, route_data: TransitRouteCreate) -> Optional[TransitRouteWithDetails]:
        query = select(TransitRoute).where(TransitRoute.id == route_id)
        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return None

        # Update route fields
        route.name = route_data.name
        route.description = route_data.description
        route.status = route_data.status
        route.total_stations = len(route_data.stops)
        route.estimated_time = route_data.estimated_time

        # Delete existing stops and create new ones
        await self.db.execute(delete(RouteStop).where(RouteStop.transit_route_id == route_id))

        for stop in route_data.stops:
            route_stop = RouteStop(
                transit_route_id=route_id,
                station_id=stop.station_id,
                stop_order=stop.stop_order
            )
            self.db.add(route_stop)

        await self.db.commit()

        return await self.get_transit_route(route_id)

    async def delete_transit_route(self, route_id: int) -> bool:
        query = select(TransitRoute).where(TransitRoute.id == route_id)
        result = await self.db.execute(query)
        route = result.scalar_one_or_none()

        if not route:
            return False

        # Delete route stops first (cascade should handle this but being explicit)
        await self.db.execute(delete(RouteStop).where(RouteStop.transit_route_id == route_id))

        # Delete route
        await self.db.delete(route)
        await self.db.commit()
        return True