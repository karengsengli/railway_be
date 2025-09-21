from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from .service import RouteService
from .schemas import RouteWithDetails, RouteCreate

router = APIRouter()

@router.get("/", response_model=List[RouteWithDetails])
async def get_routes(
    skip: int = 0,
    limit: int = 100,
    line_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    service = RouteService(db)
    return await service.get_routes(skip=skip, limit=limit, line_id=line_id)

@router.get("/{route_id}", response_model=RouteWithDetails)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = RouteService(db)
    route = await service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.post("/", response_model=RouteWithDetails, status_code=201)
async def create_route(
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = RouteService(db)
    return await service.create_route(route_data)

@router.put("/{route_id}", response_model=RouteWithDetails)
async def update_route(
    route_id: int,
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db)
):
    service = RouteService(db)
    updated_route = await service.update_route(route_id, route_data)
    if not updated_route:
        raise HTTPException(status_code=404, detail="Route not found")
    return updated_route

@router.delete("/{route_id}", status_code=204)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = RouteService(db)
    success = await service.delete_route(route_id)
    if not success:
        raise HTTPException(status_code=404, detail="Route not found")