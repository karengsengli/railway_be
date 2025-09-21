from pydantic import BaseModel, validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# RouteSegment Schemas
class RouteSegmentBase(BaseModel):
    from_station_id: int
    to_station_id: int
    distance_km: Decimal
    duration_minutes: int
    transport_type: str = "train"

    @validator('from_station_id', 'to_station_id')
    def station_ids_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Station IDs must be positive')
        return v

    @validator('distance_km')
    def distance_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Distance must be positive')
        return v

    @validator('duration_minutes')
    def duration_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Duration must be positive')
        return v

    @validator('to_station_id')
    def stations_must_be_different(cls, v, values):
        if 'from_station_id' in values and v == values['from_station_id']:
            raise ValueError('From and to stations must be different')
        return v

class RouteSegmentCreate(RouteSegmentBase):
    pass

class RouteSegmentUpdate(BaseModel):
    from_station_id: Optional[int] = None
    to_station_id: Optional[int] = None
    distance_km: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    transport_type: Optional[str] = None

class RouteSegmentResponse(RouteSegmentBase):
    id: int
    train_route_id: int
    segment_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    # Station names for display
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None

    class Config:
        from_attributes = True

# TrainRoute Schemas
class TrainRouteBase(BaseModel):
    name: str
    description: Optional[str] = None

class TrainRouteCreate(TrainRouteBase):
    line_id: int

class TrainRouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TrainRouteResponse(TrainRouteBase):
    id: int
    line_id: int
    total_distance_km: Optional[Decimal] = None
    total_duration_minutes: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Line information for display
    line_name: Optional[str] = None
    line_color: Optional[str] = None

    # Route segments
    route_segments: List[RouteSegmentResponse] = []

    class Config:
        from_attributes = True

# Bulk operations
class RouteSegmentBulkCreate(BaseModel):
    segments: List[RouteSegmentCreate]

class RouteSegmentMoveRequest(BaseModel):
    direction: str  # "up" or "down"

    @validator('direction')
    def direction_must_be_valid(cls, v):
        if v not in ['up', 'down']:
            raise ValueError('Direction must be "up" or "down"')
        return v

class RouteSegmentReorderRequest(BaseModel):
    new_order: int

    @validator('new_order')
    def order_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Order must be positive')
        return v

# Response models for operations
class RouteOperationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None