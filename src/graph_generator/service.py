from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from typing import Dict, List, Set, Tuple
from datetime import datetime
import logging

from ..models import (
    Station, TrainLine, TrainCompany, RouteSegment, TrainRoute,
    IntersectionPoint, IntersectionSegment
)

logger = logging.getLogger(__name__)

class GraphGeneratorService:

    @staticmethod
    def is_real_station_name(name: str) -> bool:
        """
        Check if station name is a real name (not a generated code like N1, E1, S1)
        """
        import re
        # Filter out code-like patterns: N1, E1, S1, etc.
        code_pattern = re.compile(r'^[NESW]\d+$|^[A-Z]\d+$')
        return not code_pattern.match(name)

    @staticmethod
    async def build_graph_from_route_segments(db: AsyncSession) -> Dict[str, List[str]]:
        """
        Build adjacency list graph from RouteSegment data using only real station names
        """
        graph = {}

        # Get all route segments with station details
        result = await db.execute(
            select(RouteSegment)
            .options(
                selectinload(RouteSegment.from_station),
                selectinload(RouteSegment.to_station)
            )
            .where(RouteSegment.status == "active")
            .order_by(RouteSegment.train_route_id, RouteSegment.segment_order)
        )

        route_segments = result.scalars().all()

        for segment in route_segments:
            if segment.from_station and segment.to_station:
                from_name = segment.from_station.name
                to_name = segment.to_station.name

                # Only include real station names, skip generated codes
                if (GraphGeneratorService.is_real_station_name(from_name) and
                    GraphGeneratorService.is_real_station_name(to_name)):

                    # Add bidirectional connection (trains go both ways)
                    if from_name not in graph:
                        graph[from_name] = []
                    if to_name not in graph:
                        graph[to_name] = []

                    if to_name not in graph[from_name]:
                        graph[from_name].append(to_name)
                    if from_name not in graph[to_name]:
                        graph[to_name].append(from_name)

        return graph

    @staticmethod
    async def add_intersection_segments_to_graph(db: AsyncSession, graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Add intersection/transfer connections to the graph using only real station names
        """
        # Get all intersection segments with station details
        result = await db.execute(
            select(IntersectionSegment)
            .options(
                selectinload(IntersectionSegment.from_station),
                selectinload(IntersectionSegment.to_station)
            )
            .where(IntersectionSegment.status == "active")
        )

        intersection_segments = result.scalars().all()

        for segment in intersection_segments:
            if segment.from_station and segment.to_station:
                from_name = segment.from_station.name
                to_name = segment.to_station.name

                # Only include real station names, skip generated codes
                if (GraphGeneratorService.is_real_station_name(from_name) and
                    GraphGeneratorService.is_real_station_name(to_name)):

                    # Add bidirectional transfer connection
                    if from_name not in graph:
                        graph[from_name] = []
                    if to_name not in graph:
                        graph[to_name] = []

                    if to_name not in graph[from_name]:
                        graph[from_name].append(to_name)
                    if from_name not in graph[to_name]:
                        graph[to_name].append(from_name)

        return graph

    @staticmethod
    async def generate_complete_graph(db: AsyncSession) -> Tuple[Dict[str, List[str]], Dict]:
        """
        Generate the complete graph including both route segments and intersections
        """
        # Start with route segments (within-line connections)
        graph = await GraphGeneratorService.build_graph_from_route_segments(db)

        # Add intersection segments (between-line transfers)
        graph = await GraphGeneratorService.add_intersection_segments_to_graph(db, graph)

        # Generate metadata
        metadata = await GraphGeneratorService.generate_metadata(db, graph)

        # Sort connections for each node for consistency
        for node in graph:
            graph[node].sort()

        return graph, metadata

    @staticmethod
    async def generate_metadata(db: AsyncSession, graph: Dict[str, List[str]]) -> Dict:
        """Generate metadata about the graph"""

        # Count total connections
        total_connections = sum(len(connections) for connections in graph.values()) // 2  # Divide by 2 for bidirectional

        # Get line information
        lines_result = await db.execute(
            select(TrainLine.name).where(TrainLine.status == "active")
        )
        lines = [line for line in lines_result.scalars().all()]

        # Count intersection points
        intersection_count_result = await db.execute(
            select(IntersectionPoint).where(IntersectionPoint.status == "active")
        )
        intersection_count = len(intersection_count_result.scalars().all())

        return {
            "total_nodes": len(graph),
            "total_connections": total_connections,
            "lines_included": lines,
            "intersection_points_count": intersection_count,
            "generated_at": datetime.now().isoformat()
        }

    @staticmethod
    async def get_graph_by_line_id(db: AsyncSession, line_id: int) -> Tuple[Dict[str, List[str]], Dict]:
        """
        Generate graph for a specific train line only using actual station names
        """
        graph = {}

        # Get route segments for specific line with station details
        result = await db.execute(
            select(RouteSegment)
            .join(TrainRoute, RouteSegment.train_route_id == TrainRoute.id)
            .where(TrainRoute.line_id == line_id)
            .where(RouteSegment.status == "active")
            .options(
                selectinload(RouteSegment.from_station),
                selectinload(RouteSegment.to_station)
            )
            .order_by(RouteSegment.segment_order)
        )

        route_segments = result.scalars().all()

        for segment in route_segments:
            if segment.from_station and segment.to_station:
                from_name = segment.from_station.name
                to_name = segment.to_station.name

                # Only include real station names, skip generated codes
                if (GraphGeneratorService.is_real_station_name(from_name) and
                    GraphGeneratorService.is_real_station_name(to_name)):

                    if from_name not in graph:
                        graph[from_name] = []
                    if to_name not in graph:
                        graph[to_name] = []

                    if to_name not in graph[from_name]:
                        graph[from_name].append(to_name)
                    if from_name not in graph[to_name]:
                        graph[to_name].append(from_name)

        # Sort connections
        for node in graph:
            graph[node].sort()

        # Generate basic metadata for single line
        line_result = await db.execute(
            select(TrainLine.name).where(TrainLine.id == line_id)
        )
        line_name = line_result.scalar_one_or_none()

        metadata = {
            "total_nodes": len(graph),
            "total_connections": sum(len(connections) for connections in graph.values()) // 2,
            "line_name": line_name,
            "generated_at": datetime.now().isoformat()
        }

        return graph, metadata

    @staticmethod
    async def get_station_name_mapping(db: AsyncSession) -> Dict[int, str]:
        """Get mapping of station_id -> station_name for all stations"""
        station_name_map = {}

        # Get all stations with their names
        result = await db.execute(
            select(Station.id, Station.name)
            .where(Station.status == "active")
            .order_by(Station.id)
        )

        for station in result.all():
            station_name_map[station.id] = station.name

        return station_name_map

    @staticmethod
    async def get_graph_by_routes(db: AsyncSession, include_intersections: bool = True) -> Dict[str, Dict[str, List[str]]]:
        """
        Generate graph data organized by train routes/lines
        Returns: {"Line Name": {"Station": ["Connected Stations"]}}
        """
        routes_data = {}

        # Get all active train lines
        lines_result = await db.execute(
            select(TrainLine.id, TrainLine.name)
            .where(TrainLine.status == "active")
            .order_by(TrainLine.name)
        )
        lines = lines_result.all()

        # For each line, get its graph
        for line_id, line_name in lines:
            line_graph, _ = await GraphGeneratorService.get_graph_by_line_id(db, line_id)
            if line_graph:  # Only include lines that have data
                routes_data[line_name] = line_graph

        # If intersections are enabled, add them to relevant lines
        if include_intersections:
            # Get intersection segments
            result = await db.execute(
                select(IntersectionSegment)
                .options(
                    selectinload(IntersectionSegment.from_station),
                    selectinload(IntersectionSegment.to_station)
                )
                .where(IntersectionSegment.status == "active")
            )
            intersection_segments = result.scalars().all()

            # Add intersection connections to the appropriate lines
            for segment in intersection_segments:
                if segment.from_station and segment.to_station:
                    from_name = segment.from_station.name
                    to_name = segment.to_station.name

                    # Only include real station names
                    if (GraphGeneratorService.is_real_station_name(from_name) and
                        GraphGeneratorService.is_real_station_name(to_name)):

                        # Find which lines these stations belong to and add the connections
                        for line_name, line_graph in routes_data.items():
                            if from_name in line_graph:
                                if to_name not in line_graph[from_name]:
                                    line_graph[from_name].append(to_name)
                                    line_graph[from_name].sort()
                            if to_name in line_graph:
                                if from_name not in line_graph[to_name]:
                                    line_graph[to_name].append(from_name)
                                    line_graph[to_name].sort()

        return routes_data