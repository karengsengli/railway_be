from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime

class RouteStopBase(BaseModel):
    station_id: int
    stop_order: int

class RouteStopCreate(BaseModel):
    station_id: int
    stop_order: int  # This will be the main field used by the service

    # Allow but ignore extra fields from frontend
    class Config:
        extra = "ignore"

    def __init__(self, **data):
        # Handle the case where frontend sends 'order' instead of 'stop_order'
        if 'order' in data and 'stop_order' not in data:
            data['stop_order'] = data['order']
            # Remove 'order' so it doesn't cause validation issues
            data.pop('order', None)

        super().__init__(**data)

class RouteStop(RouteStopBase):
    id: int
    transit_route_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RouteStopWithDetails(RouteStop):
    station_name: Optional[str] = None
    order: int
    lines: List[dict] = []

    def __init__(self, **data):
        if 'stop_order' in data:
            data['order'] = data['stop_order']
        super().__init__(**data)

class TransitRouteBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    estimated_time: Optional[str] = None

class TransitRouteCreate(TransitRouteBase):
    stops: List[RouteStopCreate] = []

    # Allow but ignore extra fields from frontend (like total_stations)
    class Config:
        extra = "ignore"

class TransitRoute(TransitRouteBase):
    id: int
    total_stations: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransitRouteWithDetails(TransitRoute):
    stops: List[RouteStopWithDetails] = []