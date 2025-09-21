from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional
import heapq

from ..models import Route, Station, TrainLine
from .schemas import DistanceCalculationResponse, RouteSegmentInfo, DistanceCalculationRequest

class DistanceCalculationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_distance_and_time(self, request: DistanceCalculationRequest) -> DistanceCalculationResponse:
        """
        Calculate the shortest route between two stations using Dijkstra's algorithm
        """
        from_station_id = request.from_station_id
        to_station_id = request.to_station_id

        # First check if stations exist
        stations_query = select(Station).where(Station.id.in_([from_station_id, to_station_id]))
        stations_result = await self.db.execute(stations_query)
        stations = {station.id: station for station in stations_result.scalars().all()}

        if from_station_id not in stations:
            return DistanceCalculationResponse(
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                from_station_name="Unknown",
                to_station_name=stations.get(to_station_id, {}).name if to_station_id in stations else "Unknown",
                total_distance_km=0.0,
                total_duration_minutes=0,
                route_segments=[],
                success=False,
                message=f"From station with ID {from_station_id} not found"
            )

        if to_station_id not in stations:
            return DistanceCalculationResponse(
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                from_station_name=stations[from_station_id].name,
                to_station_name="Unknown",
                total_distance_km=0.0,
                total_duration_minutes=0,
                route_segments=[],
                success=False,
                message=f"To station with ID {to_station_id} not found"
            )

        # If it's the same station
        if from_station_id == to_station_id:
            return DistanceCalculationResponse(
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                from_station_name=stations[from_station_id].name,
                to_station_name=stations[to_station_id].name,
                total_distance_km=0.0,
                total_duration_minutes=0,
                route_segments=[],
                success=True,
                message="Same station selected"
            )

        # Load all routes with station and line information
        routes_query = select(Route).options(
            selectinload(Route.from_station),
            selectinload(Route.to_station),
            selectinload(Route.line)
        ).where(Route.status == "active")

        routes_result = await self.db.execute(routes_query)
        routes = routes_result.scalars().all()

        if not routes:
            return DistanceCalculationResponse(
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                from_station_name=stations[from_station_id].name,
                to_station_name=stations[to_station_id].name,
                total_distance_km=0.0,
                total_duration_minutes=0,
                route_segments=[],
                success=False,
                message="No active routes found in the system"
            )

        # Build adjacency graph
        graph = {}
        route_info = {}

        for route in routes:
            from_id = route.from_station_id
            to_id = route.to_station_id

            # Add bidirectional edges (assuming trains can go both ways)
            if from_id not in graph:
                graph[from_id] = []
            if to_id not in graph:
                graph[to_id] = []

            distance = float(route.distance_km) if route.distance_km else 1.0
            duration = route.duration_minutes if route.duration_minutes else 10

            graph[from_id].append((to_id, distance, duration))
            graph[to_id].append((from_id, distance, duration))

            # Store route information for both directions
            route_info[(from_id, to_id)] = route
            route_info[(to_id, from_id)] = route

        # Run Dijkstra's algorithm to find shortest path
        shortest_path = await self._find_shortest_path(
            graph, from_station_id, to_station_id
        )

        if not shortest_path:
            return DistanceCalculationResponse(
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                from_station_name=stations[from_station_id].name,
                to_station_name=stations[to_station_id].name,
                total_distance_km=0.0,
                total_duration_minutes=0,
                route_segments=[],
                success=False,
                message="No route found between the selected stations"
            )

        # Build route segments from the path
        route_segments = []
        total_distance = 0.0
        total_duration = 0

        for i in range(len(shortest_path) - 1):
            current_station_id = shortest_path[i]
            next_station_id = shortest_path[i + 1]

            route = route_info.get((current_station_id, next_station_id))
            if route:
                segment_distance = float(route.distance_km) if route.distance_km else 1.0
                segment_duration = route.duration_minutes if route.duration_minutes else 10

                segment = RouteSegmentInfo(
                    from_station_id=current_station_id,
                    to_station_id=next_station_id,
                    from_station_name=stations[current_station_id].name,
                    to_station_name=stations[next_station_id].name,
                    line_name=route.line.name if route.line else "Unknown Line",
                    distance_km=segment_distance,
                    duration_minutes=segment_duration
                )
                route_segments.append(segment)
                total_distance += segment_distance
                total_duration += segment_duration

        return DistanceCalculationResponse(
            from_station_id=from_station_id,
            to_station_id=to_station_id,
            from_station_name=stations[from_station_id].name,
            to_station_name=stations[to_station_id].name,
            total_distance_km=round(total_distance, 2),
            total_duration_minutes=total_duration,
            route_segments=route_segments,
            success=True,
            message=f"Route found with {len(route_segments)} segments"
        )

    async def _find_shortest_path(self, graph: Dict, start: int, end: int) -> Optional[List[int]]:
        """
        Find shortest path using Dijkstra's algorithm
        Returns list of station IDs representing the path
        """
        if start not in graph or end not in graph:
            return None

        # Priority queue: (distance, duration, current_node, path)
        pq = [(0.0, 0, start, [start])]
        visited = set()

        while pq:
            current_distance, current_duration, current_node, path = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == end:
                return path

            if current_node in graph:
                for neighbor, edge_distance, edge_duration in graph[current_node]:
                    if neighbor not in visited:
                        new_distance = current_distance + edge_distance
                        new_duration = current_duration + edge_duration
                        new_path = path + [neighbor]
                        heapq.heappush(pq, (new_distance, new_duration, neighbor, new_path))

        return None