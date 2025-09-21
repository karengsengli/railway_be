from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class RouteBase(BaseModel):
    line_id: int
    from_station_id: int
    to_station_id: int
    transport_type: str = "train"
    distance_km: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    station_count: Optional[int] = None
    status: str = "active"

class RouteCreate(RouteBase):
    pass

class Route(RouteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RouteWithDetails(Route):
    line_name: Optional[str] = None
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None