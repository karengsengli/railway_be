from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TrainCompanyBase(BaseModel):
    name: str
    code: str
    status: Optional[str] = "active"
    region_id: int
    website: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None

class TrainCompanyCreate(TrainCompanyBase):
    pass

class TrainCompanyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None
    region_id: Optional[int] = None
    website: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None

class TrainCompany(TrainCompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainCompanyWithRegion(TrainCompany):
    region_name: Optional[str] = None
    region_country: Optional[str] = None

class CompanySearchResult(BaseModel):
    companies: List[TrainCompanyWithRegion]
    total_count: int