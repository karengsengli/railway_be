from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models import Journey, JourneySegment
from .schemas import JourneyCreate, JourneyWithDetails
from ..models import Station

class JourneyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_journey(self, journey: JourneyCreate, user_id: int) -> Journey:
        db_journey = Journey(**journey.model_dump(), user_id=user_id)
        self.db.add(db_journey)
        await self.db.commit()
        await self.db.refresh(db_journey)
        return db_journey

    async def get_journeys(self, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[JourneyWithDetails]:
        query = select(Journey).options(
            selectinload(Journey.from_station),
            selectinload(Journey.to_station),
            selectinload(Journey.journey_segments)
        )

        if user_id:
            query = query.where(Journey.user_id == user_id)

        query = query.offset(skip).limit(limit).order_by(Journey.created_at.desc())
        result = await self.db.execute(query)
        journeys = result.scalars().all()

        journeys_with_details = []
        for journey in journeys:
            journey_data = JourneyWithDetails(
                id=journey.id,
                user_id=journey.user_id,
                from_station_id=journey.from_station_id,
                to_station_id=journey.to_station_id,
                departure_time=journey.departure_time,
                arrival_time=journey.arrival_time,
                total_cost=journey.total_cost,
                passenger_count=journey.passenger_count,
                status=journey.status,
                created_at=journey.created_at,
                updated_at=journey.updated_at,
                from_station_name=journey.from_station.name if journey.from_station else None,
                to_station_name=journey.to_station.name if journey.to_station else None,
                journey_segments=journey.journey_segments
            )
            journeys_with_details.append(journey_data)

        return journeys_with_details

    async def get_journey(self, journey_id: int) -> Optional[JourneyWithDetails]:
        query = select(Journey).options(
            selectinload(Journey.from_station),
            selectinload(Journey.to_station),
            selectinload(Journey.journey_segments)
        ).where(Journey.id == journey_id)

        result = await self.db.execute(query)
        journey = result.scalar_one_or_none()

        if not journey:
            return None

        return JourneyWithDetails(
            id=journey.id,
            user_id=journey.user_id,
            from_station_id=journey.from_station_id,
            to_station_id=journey.to_station_id,
            departure_time=journey.departure_time,
            arrival_time=journey.arrival_time,
            total_cost=journey.total_cost,
            passenger_count=journey.passenger_count,
            status=journey.status,
            created_at=journey.created_at,
            updated_at=journey.updated_at,
            from_station_name=journey.from_station.name if journey.from_station else None,
            to_station_name=journey.to_station.name if journey.to_station else None,
            journey_segments=journey.journey_segments
        )

    async def update_journey(self, journey_id: int, journey_data: JourneyCreate) -> Optional[JourneyWithDetails]:
        query = select(Journey).where(Journey.id == journey_id)
        result = await self.db.execute(query)
        journey = result.scalar_one_or_none()

        if not journey:
            return None

        for field, value in journey_data.model_dump(exclude_unset=True).items():
            setattr(journey, field, value)

        await self.db.commit()
        await self.db.refresh(journey)

        return await self.get_journey(journey_id)

    async def delete_journey(self, journey_id: int) -> bool:
        query = select(Journey).where(Journey.id == journey_id)
        result = await self.db.execute(query)
        journey = result.scalar_one_or_none()

        if not journey:
            return False

        await self.db.delete(journey)
        await self.db.commit()
        return True