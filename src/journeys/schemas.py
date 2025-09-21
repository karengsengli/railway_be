from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class JourneySegmentBase(BaseModel):
    route_id: int
    segment_order: int
    from_station_id: int
    to_station_id: int
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    cost: Optional[Decimal] = None
    instructions: Optional[str] = None

class JourneySegment(JourneySegmentBase):
    id: int
    journey_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JourneyBase(BaseModel):
    from_station_id: int
    to_station_id: int
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    total_cost: Optional[Decimal] = None
    passenger_count: Optional[Dict[str, Any]] = None
    status: str = "planned"

class JourneyCreate(JourneyBase):
    pass

class Journey(JourneyBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JourneyWithDetails(Journey):
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None
    journey_segments: List[JourneySegment] = []