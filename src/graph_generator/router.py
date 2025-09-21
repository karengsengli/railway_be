from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from .service import GraphGeneratorService
from .schemas import GraphResponse

router = APIRouter(prefix="/graph", tags=["Graph Generator"])

@router.get("/routes")
async def generate_routes_graph_by_route(
    include_intersections: bool = Query(True, description="Include intersection/transfer connections"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a graph/linked list representation organized by train routes.

    Returns format:
    {
        "Sukhumvit Line": {
            "Khu Khot": ["Yaek Kor Por Aor"],
            "Yaek Kor Por Aor": ["Khu Khot", "Royal Thai Air Force Museum"],
            ...
        },
        "Silom Line": {
            "Ratchadamri": ["Sala Daeng"],
            "Sala Daeng": ["Ratchadamri", "Chong Nonsi"],
            ...
        }
    }

    Parameters:
    - include_intersections: Whether to include transfer connections between lines
    """
    try:
        routes_data = await GraphGeneratorService.get_graph_by_routes(db, include_intersections)
        return routes_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating routes graph: {str(e)}")

@router.get("/routes/single")
async def generate_single_route_graph(
    line_id: int = Query(..., description="Line ID for specific route"),
    include_intersections: bool = Query(False, description="Include intersection/transfer connections"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate graph for a single specific train line.

    Returns adjacency list for just one line:
    {
        "Khu Khot": ["Yaek Kor Por Aor"],
        "Yaek Kor Por Aor": ["Khu Khot", "Royal Thai Air Force Museum"],
        ...
    }
    """
    try:
        graph, _ = await GraphGeneratorService.get_graph_by_line_id(db, line_id)
        return graph

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")

@router.get("/routes/adjacency-list")
async def get_adjacency_list_only(
    include_intersections: bool = Query(True, description="Include intersection/transfer connections"),
    line_id: Optional[int] = Query(None, description="Generate graph for specific line only"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get only the adjacency list representation without metadata.
    Returns the exact format you requested.
    """
    try:
        if line_id:
            graph, _ = await GraphGeneratorService.get_graph_by_line_id(db, line_id)
        elif include_intersections:
            # Generate complete graph with both route segments and intersections
            graph, _ = await GraphGeneratorService.generate_complete_graph(db)
        else:
            # Generate graph from route segments only (no transfers)
            graph = await GraphGeneratorService.build_graph_from_route_segments(db)

        return graph

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating adjacency list: {str(e)}")

@router.get("/station-names")
async def get_station_name_mapping(db: AsyncSession = Depends(get_db)):
    """
    Get mapping of station IDs to station names for debugging.
    """
    try:
        station_name_map = await GraphGeneratorService.get_station_name_mapping(db)
        return {"station_name_mapping": station_name_map}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting station names: {str(e)}")

@router.get("/routes/metadata")
async def get_graph_metadata(
    include_intersections: bool = Query(True, description="Include intersection/transfer connections"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get metadata about the graph without the full adjacency list.
    """
    try:
        if include_intersections:
            graph, metadata = await GraphGeneratorService.generate_complete_graph(db)
        else:
            graph = await GraphGeneratorService.build_graph_from_route_segments(db)
            metadata = await GraphGeneratorService.generate_metadata(db, graph)

        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating metadata: {str(e)}")