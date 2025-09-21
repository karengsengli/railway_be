from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from .service import LineService
from .schemas import TrainLineCreate, TrainLineUpdate, TrainLineWithCompany, LineSearchResult

router = APIRouter()

@router.get("/", response_model=LineSearchResult)
async def get_lines(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    region_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = LineService(db)
    return await service.get_lines(
        skip=skip,
        limit=limit,
        company_id=company_id,
        region_id=region_id,
        search=search
    )

@router.get("/search", response_model=List[TrainLineWithCompany])
async def search_lines(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    service = LineService(db)
    return await service.search_lines(q, limit)

@router.get("/company/{company_id}", response_model=List[TrainLineWithCompany])
async def get_lines_by_company(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = LineService(db)
    return await service.get_lines_by_company(company_id)

@router.get("/{line_id}", response_model=TrainLineWithCompany)
async def get_line(
    line_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = LineService(db)
    line = await service.get_line(line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    return line

@router.post("/", response_model=TrainLineWithCompany, status_code=201)
async def create_line(line_data: TrainLineCreate, db: AsyncSession = Depends(get_db)):
    service = LineService(db)
    line = await service.create_line(line_data)
    await db.commit()

    # Return with company info
    return await service.get_line(line.id)

@router.put("/{line_id}", response_model=TrainLineWithCompany)
async def update_line(
    line_id: int,
    line_data: TrainLineUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = LineService(db)
    line = await service.update_line(line_id, line_data)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    await db.commit()

    # Return with company info
    return await service.get_line(line.id)

@router.delete("/{line_id}", status_code=204)
async def delete_line(line_id: int, db: AsyncSession = Depends(get_db)):
    service = LineService(db)
    try:
        success = await service.delete_line(line_id)
        if not success:
            raise HTTPException(status_code=404, detail="Line not found")

        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete line")