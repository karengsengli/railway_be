from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Intersection Point Schemas
class IntersectionPointCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lat: Optional[Decimal] = None
    long: Optional[Decimal] = None
    station_codes: Optional[List[str]] = None
    accessibility_features: Optional[Dict[str, Any]] = None

class IntersectionPointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lat: Optional[Decimal] = None
    long: Optional[Decimal] = None
    station_codes: Optional[List[str]] = None
    accessibility_features: Optional[Dict[str, Any]] = None

class IntersectionPointResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    lat: Optional[Decimal] = None
    long: Optional[Decimal] = None
    station_codes: Optional[List[str]] = None
    accessibility_features: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Intersection Segment Schemas
class IntersectionSegmentCreate(BaseModel):
    intersection_point_id: int
    from_station_id: int
    to_station_id: int
    from_line_id: int
    to_line_id: int
    distance_km: Decimal
    duration_minutes: int
    transport_type: str = "walk"
    transfer_cost: Optional[Decimal] = Decimal('0.00')
    direction_instructions: Optional[str] = None
    accessibility_notes: Optional[str] = None

    @validator('distance_km')
    def validate_distance(cls, v):
        if v <= 0:
            raise ValueError('Distance must be greater than 0')
        return v

    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Duration must be greater than 0')
        return v

    @validator('from_station_id', 'to_station_id')
    def validate_different_stations(cls, v, values):
        if 'from_station_id' in values and v == values.get('from_station_id'):
            raise ValueError('From and to stations must be different')
        return v

class IntersectionSegmentUpdate(BaseModel):
    intersection_point_id: Optional[int] = None
    from_station_id: Optional[int] = None
    to_station_id: Optional[int] = None
    from_line_id: Optional[int] = None
    to_line_id: Optional[int] = None
    distance_km: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    transport_type: Optional[str] = None
    transfer_cost: Optional[Decimal] = None
    direction_instructions: Optional[str] = None
    accessibility_notes: Optional[str] = None

    @validator('distance_km')
    def validate_distance(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Distance must be greater than 0')
        return v

    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration must be greater than 0')
        return v

class IntersectionSegmentResponse(BaseModel):
    id: int
    intersection_point_id: int
    from_station_id: int
    to_station_id: int
    from_line_id: int
    to_line_id: int
    distance_km: Decimal
    duration_minutes: int
    transport_type: str
    transfer_cost: Optional[Decimal] = None
    direction_instructions: Optional[str] = None
    accessibility_notes: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Additional fields for easier display
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None
    from_line_name: Optional[str] = None
    to_line_name: Optional[str] = None
    from_line_color: Optional[str] = None
    to_line_color: Optional[str] = None
    intersection_point_name: Optional[str] = None

    class Config:
        from_attributes = True

# Response Schemas
class IntersectionOperationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Combined Response for Intersection Points with Segments
class IntersectionPointWithSegmentsResponse(IntersectionPointResponse):
    intersection_segments: List[IntersectionSegmentResponse] = []

    class Config:
        from_attributes = True