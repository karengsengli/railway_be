from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class RegionBase(BaseModel):
    name: str
    country: str
    timezone: Optional[str] = "UTC"
    currency: Optional[str] = "USD"

class Region(RegionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainCompanyBase(BaseModel):
    name: str
    code: str
    status: Optional[str] = "active"
    region_id: int
    website: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None

class TrainCompany(TrainCompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainLineBase(BaseModel):
    company_id: int
    name: str
    color: Optional[str] = None
    status: Optional[str] = "active"

class TrainLine(TrainLineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainLineWithCompany(TrainLine):
    company_name: Optional[str] = None
    region_name: Optional[str] = None

class StationBase(BaseModel):
    line_id: Optional[int] = None
    name: str
    code: Optional[str] = None
    lat: Optional[Decimal] = None
    long: Optional[Decimal] = None  # Changed from lng to long to match database
    is_interchange: Optional[bool] = False
    status: Optional[str] = "active"

class StationCreate(StationBase):
    pass

class Station(StationBase):
    id: int
    created_at: Optional[datetime] = None  # Allow null datetime values
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StationWithLine(Station):
    line_name: Optional[str] = None
    company_name: Optional[str] = None
    region_name: Optional[str] = None

class StationSearchResult(BaseModel):
    stations: List[StationWithLine]
    total_count: int