from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class RouteSegmentBase(BaseModel):
    from_station_id: int
    to_station_id: int
    transport_type: str = "train"
    distance_km: Decimal = Field(..., ge=0)
    duration_minutes: int = Field(..., ge=1)
    order: int = Field(..., ge=1)

class RouteSegmentCreate(RouteSegmentBase):
    pass

class RouteSegment(RouteSegmentBase):
    id: int
    route_id: int
    created_at: datetime
    updated_at: datetime
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None

    class Config:
        from_attributes = True

class UnifiedRouteBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    line_id: int
    status: str = "active"

class UnifiedRouteCreate(UnifiedRouteBase):
    segments: List[RouteSegmentCreate] = Field(..., min_items=1)

class UnifiedRouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    line_id: Optional[int] = None
    status: Optional[str] = None
    segments: Optional[List[RouteSegmentCreate]] = None

class UnifiedRoute(UnifiedRouteBase):
    id: int
    total_distance: Decimal
    total_duration: int
    created_at: datetime
    updated_at: datetime
    line_name: Optional[str] = None
    segments: List[RouteSegment] = []

    class Config:
        from_attributes = True

class UnifiedRouteResponse(BaseModel):
    routes: List[UnifiedRoute]
    total: int