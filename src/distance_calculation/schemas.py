from pydantic import BaseModel
from typing import List, Optional

class DistanceCalculationRequest(BaseModel):
    from_station_id: int
    to_station_id: int

class RouteSegmentInfo(BaseModel):
    from_station_id: int
    to_station_id: int
    from_station_name: str
    to_station_name: str
    line_name: str
    distance_km: float
    duration_minutes: int

class DistanceCalculationResponse(BaseModel):
    from_station_id: int
    to_station_id: int
    from_station_name: str
    to_station_name: str
    total_distance_km: float
    total_duration_minutes: int
    route_segments: List[RouteSegmentInfo]
    success: bool
    message: Optional[str] = None