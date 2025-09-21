from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import TrainLine, TrainCompany, Region, Station
from .schemas import TrainLineCreate, TrainLineUpdate, TrainLineWithCompany, LineSearchResult

class LineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lines(
        self,
        skip: int = 0,
        limit: int = 100,
        company_id: Optional[int] = None,
        region_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> LineSearchResult:

        query = select(TrainLine).options(
            selectinload(TrainLine.company).selectinload(TrainCompany.region)
        )

        if company_id:
            query = query.where(TrainLine.company_id == company_id)

        if region_id:
            query = query.join(TrainCompany).where(TrainCompany.region_id == region_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(TrainLine.name.ilike(search_pattern))

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # Get paginated results
        query = query.order_by(TrainLine.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        lines = result.scalars().all()

        # Convert to response schema
        lines_with_company = []
        for line in lines:
            line_data = TrainLineWithCompany(
                id=line.id,
                name=line.name,
                company_id=line.company_id,
                color=line.color,
                status=line.status,
                created_at=line.created_at,
                updated_at=line.updated_at,
                company_name=line.company.name if line.company else None,
                region_name=line.company.region.name if line.company and line.company.region else None,
                region_country=line.company.region.country if line.company and line.company.region else None,
            )
            lines_with_company.append(line_data)

        return LineSearchResult(
            lines=lines_with_company,
            total_count=total_count
        )

    async def get_line(self, line_id: int) -> Optional[TrainLineWithCompany]:
        query = select(TrainLine).options(
            selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(TrainLine.id == line_id)

        result = await self.db.execute(query)
        line = result.scalar_one_or_none()

        if not line:
            return None

        return TrainLineWithCompany(
            id=line.id,
            name=line.name,
            company_id=line.company_id,
            color=line.color,
            status=line.status,
            created_at=line.created_at,
            updated_at=line.updated_at,
            company_name=line.company.name if line.company else None,
            region_name=line.company.region.name if line.company and line.company.region else None,
            region_country=line.company.region.country if line.company and line.company.region else None,
        )

    async def search_lines(self, q: str, limit: int = 10) -> List[TrainLineWithCompany]:
        search_pattern = f"%{q}%"
        query = select(TrainLine).options(
            selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(TrainLine.name.ilike(search_pattern)).order_by(TrainLine.name).limit(limit)

        result = await self.db.execute(query)
        lines = result.scalars().all()

        return [
            TrainLineWithCompany(
                id=line.id,
                name=line.name,
                company_id=line.company_id,
                color=line.color,
                status=line.status,
                created_at=line.created_at,
                updated_at=line.updated_at,
                company_name=line.company.name if line.company else None,
                region_name=line.company.region.name if line.company and line.company.region else None,
                region_country=line.company.region.country if line.company and line.company.region else None,
            )
            for line in lines
        ]

    async def create_line(self, line_data: TrainLineCreate) -> TrainLine:
        line = TrainLine(**line_data.model_dump())
        self.db.add(line)
        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def update_line(self, line_id: int, line_data: TrainLineUpdate) -> Optional[TrainLine]:
        query = select(TrainLine).where(TrainLine.id == line_id)
        result = await self.db.execute(query)
        line = result.scalar_one_or_none()

        if not line:
            return None

        # Update only provided fields
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)

        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def delete_line(self, line_id: int) -> bool:
        query = select(TrainLine).where(TrainLine.id == line_id)
        result = await self.db.execute(query)
        line = result.scalar_one_or_none()

        if not line:
            return False

        # Check if line has stations before deletion
        stations_query = select(func.count(Station.id)).where(Station.line_id == line_id)
        stations_result = await self.db.execute(stations_query)
        stations_count = stations_result.scalar()

        if stations_count > 0:
            raise ValueError(
                f"Cannot delete line with {stations_count} existing stations. "
                "Please delete all stations first."
            )

        try:
            # Use direct SQL DELETE instead of ORM delete to bypass caching issues
            from sqlalchemy import text
            delete_stmt = text("DELETE FROM train_lines WHERE id = :line_id")
            result = await self.db.execute(delete_stmt, {"line_id": line_id})
            await self.db.flush()
            return result.rowcount > 0
        except Exception as e:
            # Handle any remaining database constraint errors
            if "RESTRICT" in str(e) or "foreign key" in str(e).lower():
                raise ValueError(
                    "Cannot delete line with existing stations. "
                    "Please delete all related data first."
                )
            raise

    async def get_lines_by_company(self, company_id: int) -> List[TrainLineWithCompany]:
        query = select(TrainLine).options(
            selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(TrainLine.company_id == company_id).order_by(TrainLine.name)

        result = await self.db.execute(query)
        lines = result.scalars().all()

        return [
            TrainLineWithCompany(
                id=line.id,
                name=line.name,
                company_id=line.company_id,
                color=line.color,
                status=line.status,
                created_at=line.created_at,
                updated_at=line.updated_at,
                company_name=line.company.name if line.company else None,
                region_name=line.company.region.name if line.company and line.company.region else None,
                region_country=line.company.region.country if line.company and line.company.region else None,
            )
            for line in lines
        ]

    async def create_line(self, line_data: TrainLineCreate) -> TrainLine:
        line = TrainLine(**line_data.model_dump())
        self.db.add(line)
        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def update_line(self, line_id: int, line_data: TrainLineUpdate) -> Optional[TrainLine]:
        query = select(TrainLine).where(TrainLine.id == line_id)
        result = await self.db.execute(query)
        line = result.scalar_one_or_none()

        if not line:
            return None

        # Update only provided fields
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)

        await self.db.flush()
        await self.db.refresh(line)
        return line

    async def delete_line(self, line_id: int) -> bool:
        query = select(TrainLine).where(TrainLine.id == line_id)
        result = await self.db.execute(query)
        line = result.scalar_one_or_none()

        if not line:
            return False

        # Check if line has stations before deletion
        stations_query = select(func.count(Station.id)).where(Station.line_id == line_id)
        stations_result = await self.db.execute(stations_query)
        stations_count = stations_result.scalar()

        if stations_count > 0:
            raise ValueError(
                f"Cannot delete line with {stations_count} existing stations. "
                "Please delete all stations first."
            )

        try:
            # Use direct SQL DELETE instead of ORM delete to bypass caching issues
            from sqlalchemy import text
            delete_stmt = text("DELETE FROM train_lines WHERE id = :line_id")
            result = await self.db.execute(delete_stmt, {"line_id": line_id})
            await self.db.flush()
            return result.rowcount > 0
        except Exception as e:
            # Handle any remaining database constraint errors
            if "RESTRICT" in str(e) or "foreign key" in str(e).lower():
                raise ValueError(
                    "Cannot delete line with existing stations. "
                    "Please delete all related data first."
                )
            raise