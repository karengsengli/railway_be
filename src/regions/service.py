from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import Region, TrainCompany, TrainLine, Station
from .schemas import RegionCreate, RegionUpdate, RegionWithStats, RegionSearchResult

class RegionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_regions(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> RegionSearchResult:

        query = select(Region)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Region.name.ilike(search_pattern),
                    Region.country.ilike(search_pattern)
                )
            )

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # Get paginated results
        query = query.order_by(Region.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        regions = result.scalars().all()

        regions_with_stats = []
        for region in regions:
            # Get statistics for each region
            stats = await self._get_region_stats(region.id)
            region_data = RegionWithStats(
                id=region.id,
                name=region.name,
                country=region.country,
                timezone=region.timezone,
                currency=region.currency,
                created_at=region.created_at,
                updated_at=region.updated_at,
                **stats
            )
            regions_with_stats.append(region_data)

        return RegionSearchResult(regions=regions_with_stats, total_count=total_count)

    async def get_region(self, region_id: int) -> Optional[RegionWithStats]:
        query = select(Region).where(Region.id == region_id)
        result = await self.db.execute(query)
        region = result.scalar_one_or_none()

        if not region:
            return None

        stats = await self._get_region_stats(region.id)
        return RegionWithStats(
            id=region.id,
            name=region.name,
            country=region.country,
            timezone=region.timezone,
            currency=region.currency,
            created_at=region.created_at,
            updated_at=region.updated_at,
            **stats
        )

    async def create_region(self, region_data: RegionCreate) -> Region:
        region = Region(**region_data.model_dump())
        self.db.add(region)
        await self.db.flush()
        await self.db.refresh(region)
        return region

    async def update_region(self, region_id: int, region_data: RegionUpdate) -> Optional[Region]:
        query = select(Region).where(Region.id == region_id)
        result = await self.db.execute(query)
        region = result.scalar_one_or_none()

        if not region:
            return None

        # Update only provided fields
        update_data = region_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(region, field, value)

        await self.db.flush()
        await self.db.refresh(region)
        return region

    async def delete_region(self, region_id: int) -> bool:
        query = select(Region).where(Region.id == region_id)
        result = await self.db.execute(query)
        region = result.scalar_one_or_none()

        if not region:
            return False

        # Check if region has dependencies before deletion
        stats = await self._get_region_stats(region_id)
        if (stats["train_companies_count"] > 0 or
            stats["total_lines_count"] > 0 or
            stats["total_stations_count"] > 0):
            raise ValueError(
                "Cannot delete region with existing train companies, lines, or stations. "
                "Please delete all related data first."
            )

        try:
            print(f"DEBUG: About to delete region {region_id}")
            # Use direct SQL DELETE instead of ORM delete to bypass any caching issues
            from sqlalchemy import text
            delete_stmt = text("DELETE FROM regions WHERE id = :region_id")
            result = await self.db.execute(delete_stmt, {"region_id": region_id})
            print(f"DEBUG: Direct SQL delete executed, rows affected: {result.rowcount}")
            await self.db.flush()
            print(f"DEBUG: Flush completed successfully")
            return result.rowcount > 0
        except Exception as e:
            print(f"DEBUG: Exception during delete: {e}")
            # Handle any remaining database constraint errors
            if "RESTRICT" in str(e) or "foreign key" in str(e).lower():
                raise ValueError(
                    "Cannot delete region with existing train companies, lines, or stations. "
                    "Please delete all related data first."
                )
            raise

    async def _get_region_stats(self, region_id: int) -> dict:
        # Count train companies
        companies_query = select(func.count(TrainCompany.id)).where(TrainCompany.region_id == region_id)
        companies_result = await self.db.execute(companies_query)
        companies_count = companies_result.scalar()

        # Count total lines in this region
        lines_query = (
            select(func.count(TrainLine.id))
            .select_from(TrainLine)
            .join(TrainCompany)
            .where(TrainCompany.region_id == region_id)
        )
        lines_result = await self.db.execute(lines_query)
        lines_count = lines_result.scalar()

        # Count total stations in this region
        stations_query = (
            select(func.count(Station.id))
            .select_from(Station)
            .join(TrainLine)
            .join(TrainCompany)
            .where(TrainCompany.region_id == region_id)
        )
        stations_result = await self.db.execute(stations_query)
        stations_count = stations_result.scalar()

        return {
            "train_companies_count": companies_count,
            "total_lines_count": lines_count,
            "total_stations_count": stations_count
        }