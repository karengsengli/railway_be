from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import Station, TrainLine, TrainCompany, Region
from .schemas import StationCreate, StationWithLine, StationSearchResult

class StationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stations(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[int] = None,
        region_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> StationSearchResult:

        query = select(Station).options(
            selectinload(Station.line).selectinload(TrainLine.company).selectinload(TrainCompany.region)
        )

        if line_id:
            query = query.where(Station.line_id == line_id)

        if region_id:
            query = query.join(TrainLine).join(TrainCompany).where(TrainCompany.region_id == region_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Station.name.ilike(search_pattern),
                    Station.code.ilike(search_pattern)
                )
            )

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # Get paginated results
        query = query.order_by(Station.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        stations = result.scalars().all()

        stations_with_line = []
        for station in stations:
            station_data = StationWithLine(
                id=station.id,
                line_id=station.line_id,
                name=station.name,
                code=station.code,
                lat=station.lat,
                long=station.long,
                is_interchange=station.is_interchange,
                status=station.status,
                created_at=station.created_at,
                updated_at=station.updated_at,
                line_name=station.line.name if station.line else None,
                company_name=station.line.company.name if station.line and station.line.company else None,
                region_name=station.line.company.region.name if station.line and station.line.company and station.line.company.region else None
            )
            stations_with_line.append(station_data)

        return StationSearchResult(stations=stations_with_line, total_count=total_count)

    async def get_station(self, station_id: int) -> Optional[StationWithLine]:
        query = select(Station).options(
            selectinload(Station.line).selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(Station.id == station_id)

        result = await self.db.execute(query)
        station = result.scalar_one_or_none()

        if not station:
            return None

        return StationWithLine(
            id=station.id,
            line_id=station.line_id,
            name=station.name,
            code=station.code,
            lat=station.lat,
            long=station.long,
            is_interchange=station.is_interchange,
            platform_count=station.platform_count,
            status=station.status,
            zone_number=station.zone_number,
            created_at=station.created_at,
            updated_at=station.updated_at,
            line_name=station.line.name if station.line else None,
            company_name=station.line.company.name if station.line and station.line.company else None,
            region_name=station.line.company.region.name if station.line and station.line.company and station.line.company.region else None
        )

    async def get_stations_by_line(self, line_id: int) -> List[StationWithLine]:
        query = select(Station).options(
            selectinload(Station.line).selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(Station.line_id == line_id).order_by(Station.name)

        result = await self.db.execute(query)
        stations = result.scalars().all()

        stations_with_line = []
        for station in stations:
            station_data = StationWithLine(
                id=station.id,
                line_id=station.line_id,
                name=station.name,
                code=station.code,
                lat=station.lat,
                long=station.long,
                is_interchange=station.is_interchange,
                status=station.status,
                created_at=station.created_at,
                updated_at=station.updated_at,
                line_name=station.line.name if station.line else None,
                company_name=station.line.company.name if station.line and station.line.company else None,
                region_name=station.line.company.region.name if station.line and station.line.company and station.line.company.region else None
            )
            stations_with_line.append(station_data)

        return stations_with_line

    async def search_stations(self, search_term: str, limit: int = 10) -> List[StationWithLine]:
        search_pattern = f"%{search_term}%"
        query = select(Station).options(
            selectinload(Station.line).selectinload(TrainLine.company).selectinload(TrainCompany.region)
        ).where(
            or_(
                Station.name.ilike(search_pattern),
                Station.code.ilike(search_pattern)
            )
        ).order_by(Station.name).limit(limit)

        result = await self.db.execute(query)
        stations = result.scalars().all()

        stations_with_line = []
        for station in stations:
            station_data = StationWithLine(
                id=station.id,
                line_id=station.line_id,
                name=station.name,
                code=station.code,
                lat=station.lat,
                long=station.long,
                is_interchange=station.is_interchange,
                status=station.status,
                created_at=station.created_at,
                updated_at=station.updated_at,
                line_name=station.line.name if station.line else None,
                company_name=station.line.company.name if station.line and station.line.company else None,
                region_name=station.line.company.region.name if station.line and station.line.company and station.line.company.region else None
            )
            stations_with_line.append(station_data)

        return stations_with_line

    async def create_station(self, station_data: StationCreate) -> Station:
        station = Station(**station_data.model_dump())
        self.db.add(station)
        await self.db.flush()
        await self.db.refresh(station)
        return station

    async def update_station(self, station_id: int, station_data: StationCreate) -> Optional[Station]:
        query = select(Station).where(Station.id == station_id)
        result = await self.db.execute(query)
        station = result.scalar_one_or_none()

        if not station:
            return None

        # Update only provided fields
        update_data = station_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(station, field, value)

        await self.db.flush()
        await self.db.refresh(station)
        return station

    async def delete_station(self, station_id: int) -> bool:
        query = select(Station).where(Station.id == station_id)
        result = await self.db.execute(query)
        station = result.scalar_one_or_none()

        if not station:
            return False

        try:
            # Use direct SQL DELETE to avoid caching issues
            from sqlalchemy import text
            delete_stmt = text("DELETE FROM stations WHERE id = :station_id")
            result = await self.db.execute(delete_stmt, {"station_id": station_id})
            await self.db.flush()
            return result.rowcount > 0
        except Exception as e:
            # Handle any database constraint errors
            if "RESTRICT" in str(e) or "foreign key" in str(e).lower():
                raise ValueError(
                    "Cannot delete station with existing dependencies. "
                    "Please delete all related data first."
                )
            raise