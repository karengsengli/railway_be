from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from .service import TransitRouteService
from .schemas import TransitRouteCreate, TransitRouteWithDetails

router = APIRouter()

@router.get("/", response_model=dict)
async def get_transit_routes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    service = TransitRouteService(db)
    return await service.get_transit_routes(skip=skip, limit=limit)

@router.get("/{route_id}", response_model=TransitRouteWithDetails)
async def get_transit_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = TransitRouteService(db)
    route = await service.get_transit_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Transit route not found")
    return route

@router.post("/", response_model=TransitRouteWithDetails, status_code=201)
async def create_transit_route(
    route_data: TransitRouteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = TransitRouteService(db)
    return await service.create_transit_route(route_data)

@router.put("/{route_id}", response_model=TransitRouteWithDetails)
async def update_transit_route(
    route_id: int,
    route_data: TransitRouteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = TransitRouteService(db)
    updated_route = await service.update_transit_route(route_id, route_data)
    if not updated_route:
        raise HTTPException(status_code=404, detail="Transit route not found")
    return updated_route

@router.delete("/{route_id}", status_code=204)
async def delete_transit_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = TransitRouteService(db)
    success = await service.delete_transit_route(route_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transit route not found")