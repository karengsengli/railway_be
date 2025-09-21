from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from .service import CompanyService
from .schemas import TrainCompanyCreate, TrainCompanyUpdate, TrainCompanyWithRegion, CompanySearchResult

router = APIRouter()

@router.get("/", response_model=CompanySearchResult)
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    region_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = CompanyService(db)
    return await service.get_companies(
        skip=skip,
        limit=limit,
        region_id=region_id,
        search=search
    )

@router.get("/search", response_model=List[TrainCompanyWithRegion])
async def search_companies(
    q: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    service = CompanyService(db)
    return await service.search_companies(q, limit)

@router.get("/region/{region_id}", response_model=List[TrainCompanyWithRegion])
async def get_companies_by_region(
    region_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = CompanyService(db)
    return await service.get_companies_by_region(region_id)

@router.get("/{company_id}", response_model=TrainCompanyWithRegion)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = CompanyService(db)
    company = await service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/", response_model=TrainCompanyWithRegion, status_code=201)
async def create_company(company_data: TrainCompanyCreate, db: AsyncSession = Depends(get_db)):
    service = CompanyService(db)
    company = await service.create_company(company_data)
    await db.commit()

    # Return with region info
    return await service.get_company(company.id)

@router.put("/{company_id}", response_model=TrainCompanyWithRegion)
async def update_company(
    company_id: int,
    company_data: TrainCompanyUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = CompanyService(db)
    company = await service.update_company(company_id, company_data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await db.commit()

    # Return with region info
    return await service.get_company(company.id)

@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    service = CompanyService(db)
    try:
        success = await service.delete_company(company_id)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")

        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete company")