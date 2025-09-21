from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import TrainCompany, Region, TrainLine
from .schemas import TrainCompanyCreate, TrainCompanyUpdate, TrainCompanyWithRegion, CompanySearchResult

class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        region_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> CompanySearchResult:

        query = select(TrainCompany).options(
            selectinload(TrainCompany.region)
        )

        if region_id:
            query = query.where(TrainCompany.region_id == region_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    TrainCompany.name.ilike(search_pattern),
                    TrainCompany.code.ilike(search_pattern)
                )
            )

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # Get paginated results
        query = query.order_by(TrainCompany.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        companies = result.scalars().all()

        # Convert to response schema
        companies_with_region = []
        for company in companies:
            company_data = TrainCompanyWithRegion(
                id=company.id,
                name=company.name,
                code=company.code,
                status=company.status,
                region_id=company.region_id,
                website=company.website,
                contact_info=company.contact_info,
                created_at=company.created_at,
                updated_at=company.updated_at,
                region_name=company.region.name if company.region else None,
                region_country=company.region.country if company.region else None,
            )
            companies_with_region.append(company_data)

        return CompanySearchResult(
            companies=companies_with_region,
            total_count=total_count
        )

    async def get_company(self, company_id: int) -> Optional[TrainCompanyWithRegion]:
        query = select(TrainCompany).options(
            selectinload(TrainCompany.region)
        ).where(TrainCompany.id == company_id)

        result = await self.db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            return None

        return TrainCompanyWithRegion(
            id=company.id,
            name=company.name,
            code=company.code,
            status=company.status,
            region_id=company.region_id,
            website=company.website,
            contact_info=company.contact_info,
            created_at=company.created_at,
            updated_at=company.updated_at,
            region_name=company.region.name if company.region else None,
            region_country=company.region.country if company.region else None,
        )

    async def search_companies(self, q: str, limit: int = 10) -> List[TrainCompanyWithRegion]:
        search_pattern = f"%{q}%"
        query = select(TrainCompany).options(
            selectinload(TrainCompany.region)
        ).where(
            or_(
                TrainCompany.name.ilike(search_pattern),
                TrainCompany.code.ilike(search_pattern)
            )
        ).order_by(TrainCompany.name).limit(limit)

        result = await self.db.execute(query)
        companies = result.scalars().all()

        return [
            TrainCompanyWithRegion(
                id=company.id,
                name=company.name,
                code=company.code,
                status=company.status,
                region_id=company.region_id,
                website=company.website,
                contact_info=company.contact_info,
                created_at=company.created_at,
                updated_at=company.updated_at,
                region_name=company.region.name if company.region else None,
                region_country=company.region.country if company.region else None,
            )
            for company in companies
        ]

    async def create_company(self, company_data: TrainCompanyCreate) -> TrainCompany:
        # Validate that the region exists
        region_query = select(Region).where(Region.id == company_data.region_id)
        region_result = await self.db.execute(region_query)
        region = region_result.scalar_one_or_none()

        if not region:
            raise ValueError(f"Region with id {company_data.region_id} does not exist")

        company = TrainCompany(**company_data.model_dump())
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def update_company(self, company_id: int, company_data: TrainCompanyUpdate) -> Optional[TrainCompany]:
        query = select(TrainCompany).where(TrainCompany.id == company_id)
        result = await self.db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            return None

        # Update only provided fields
        update_data = company_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def delete_company(self, company_id: int) -> bool:
        query = select(TrainCompany).where(TrainCompany.id == company_id)
        result = await self.db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            return False

        # Check if company has train lines before deletion
        lines_query = select(func.count(TrainLine.id)).where(TrainLine.company_id == company_id)
        lines_result = await self.db.execute(lines_query)
        lines_count = lines_result.scalar()

        if lines_count > 0:
            raise ValueError(
                f"Cannot delete company with {lines_count} existing train lines. "
                "Please delete all train lines first."
            )

        try:
            # Use direct SQL DELETE instead of ORM delete to bypass caching issues
            from sqlalchemy import text
            delete_stmt = text("DELETE FROM train_companies WHERE id = :company_id")
            result = await self.db.execute(delete_stmt, {"company_id": company_id})
            await self.db.flush()
            return result.rowcount > 0
        except Exception as e:
            # Handle any remaining database constraint errors
            if "RESTRICT" in str(e) or "foreign key" in str(e).lower():
                raise ValueError(
                    "Cannot delete company with existing train lines. "
                    "Please delete all related data first."
                )
            raise

    async def get_companies_by_region(self, region_id: int) -> List[TrainCompanyWithRegion]:
        query = select(TrainCompany).options(
            selectinload(TrainCompany.region)
        ).where(TrainCompany.region_id == region_id).order_by(TrainCompany.name)

        result = await self.db.execute(query)
        companies = result.scalars().all()

        return [
            TrainCompanyWithRegion(
                id=company.id,
                name=company.name,
                code=company.code,
                status=company.status,
                region_id=company.region_id,
                website=company.website,
                contact_info=company.contact_info,
                created_at=company.created_at,
                updated_at=company.updated_at,
                region_name=company.region.name if company.region else None,
                region_country=company.region.country if company.region else None,
            )
            for company in companies
        ]