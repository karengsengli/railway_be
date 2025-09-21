from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RegionBase(BaseModel):
    name: str
    country: str
    timezone: Optional[str] = "UTC"
    currency: Optional[str] = "USD"

class RegionCreate(RegionBase):
    pass

class RegionUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None

class Region(RegionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegionWithStats(Region):
    train_companies_count: Optional[int] = 0
    total_lines_count: Optional[int] = 0
    total_stations_count: Optional[int] = 0

class RegionSearchResult(BaseModel):
    regions: List[RegionWithStats]
    total_count: int