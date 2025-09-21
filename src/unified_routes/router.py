from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List

from src.database import get_db
from src.models import TrainLine, Station
from . import crud, schemas

router = APIRouter(
    prefix="/api/unified-routes",
    tags=["unified-routes"]
)

async def enrich_routes_with_details(db: AsyncSession, routes: List[schemas.UnifiedRoute]) -> List[dict]:
    """Add line names and station names to routes"""
    enriched_routes = []

    for route in routes:
        # Get line name
        line_result = await db.execute(select(TrainLine).where(TrainLine.id == route.line_id))
        line = line_result.scalar_one_or_none()
        route_dict = route.model_dump()
        route_dict["line_name"] = line.name if line else None

        # Enrich segments with station names
        for segment in route_dict["segments"]:
            from_station_result = await db.execute(select(Station).where(Station.id == segment["from_station_id"]))
            from_station = from_station_result.scalar_one_or_none()
            to_station_result = await db.execute(select(Station).where(Station.id == segment["to_station_id"]))
            to_station = to_station_result.scalar_one_or_none()
            segment["from_station_name"] = from_station.name if from_station else None
            segment["to_station_name"] = to_station.name if to_station else None

        enriched_routes.append(route_dict)

    return enriched_routes

@router.get("/", response_model=dict)
async def get_unified_routes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    # Get routes with eager loading
    stmt = select(crud.models.UnifiedRoute).options(
        selectinload(crud.models.UnifiedRoute.segments),
        selectinload(crud.models.UnifiedRoute.line)
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    db_routes = result.scalars().all()

    # Convert to Pydantic models
    routes = [schemas.UnifiedRoute.model_validate(route) for route in db_routes]

    # Enrich with additional details
    enriched_routes = await enrich_routes_with_details(db, routes)

    return {
        "routes": enriched_routes,
        "total": len(enriched_routes)
    }

@router.get("/{route_id}", response_model=dict)
async def get_unified_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Get route with eager loading
    stmt = select(crud.models.UnifiedRoute).options(
        selectinload(crud.models.UnifiedRoute.segments),
        selectinload(crud.models.UnifiedRoute.line)
    ).where(crud.models.UnifiedRoute.id == route_id)

    result = await db.execute(stmt)
    db_route = result.scalar_one_or_none()

    if not db_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # Convert to Pydantic model
    route = schemas.UnifiedRoute.model_validate(db_route)

    # Enrich with additional details
    enriched_routes = await enrich_routes_with_details(db, [route])

    return enriched_routes[0]

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_unified_route(
    route: schemas.UnifiedRouteCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        db_route = await crud.create_unified_route(db=db, route=route)

        # Get the route with all relationships loaded
        stmt = select(crud.models.UnifiedRoute).options(
            selectinload(crud.models.UnifiedRoute.segments).selectinload(crud.models.RouteSegment.from_station),
            selectinload(crud.models.UnifiedRoute.segments).selectinload(crud.models.RouteSegment.to_station),
            selectinload(crud.models.UnifiedRoute.line)
        ).where(crud.models.UnifiedRoute.id == db_route.id)

        result = await db.execute(stmt)
        db_route_with_relations = result.scalar_one()

        # Convert to Pydantic model
        route_response = schemas.UnifiedRoute.model_validate(db_route_with_relations)

        # Enrich with additional details
        enriched_routes = await enrich_routes_with_details(db, [route_response])

        return enriched_routes[0]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create route: {str(e)}"
        )

@router.put("/{route_id}", response_model=dict)
async def update_unified_route(
    route_id: int,
    route_update: schemas.UnifiedRouteUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        db_route = await crud.update_unified_route(db=db, route_id=route_id, route_update=route_update)

        if not db_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        # Get the route with all relationships loaded
        stmt = select(crud.models.UnifiedRoute).options(
            selectinload(crud.models.UnifiedRoute.segments).selectinload(crud.models.RouteSegment.from_station),
            selectinload(crud.models.UnifiedRoute.segments).selectinload(crud.models.RouteSegment.to_station),
            selectinload(crud.models.UnifiedRoute.line)
        ).where(crud.models.UnifiedRoute.id == route_id)

        result = await db.execute(stmt)
        db_route_with_relations = result.scalar_one()

        # Convert to Pydantic model
        route_response = schemas.UnifiedRoute.model_validate(db_route_with_relations)

        # Enrich with additional details
        enriched_routes = await enrich_routes_with_details(db, [route_response])

        return enriched_routes[0]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update route: {str(e)}"
        )

@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unified_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await crud.delete_unified_route(db=db, route_id=route_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )