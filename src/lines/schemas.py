from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TrainLineBase(BaseModel):
    name: str
    company_id: int
    color: Optional[str] = None
    status: Optional[str] = "active"

class TrainLineCreate(TrainLineBase):
    pass

class TrainLineUpdate(BaseModel):
    name: Optional[str] = None
    company_id: Optional[int] = None
    color: Optional[str] = None
    status: Optional[str] = None

class TrainLine(TrainLineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainLineWithCompany(TrainLine):
    company_name: Optional[str] = None
    region_name: Optional[str] = None
    region_country: Optional[str] = None

class LineSearchResult(BaseModel):
    lines: List[TrainLineWithCompany]
    total_count: int