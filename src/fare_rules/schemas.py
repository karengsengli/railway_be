from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class PassengerTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    discount_percentage: Optional[Decimal] = 0.00
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    requires_proof: Optional[bool] = False

class PassengerTypeCreate(PassengerTypeBase):
    pass

class PassengerType(PassengerTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FareRuleBase(BaseModel):
    line_id: int
    from_station_id: int
    to_station_id: int
    passenger_type_id: int
    base_price: Decimal
    currency: Optional[str] = "THB"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    peak_hour_multiplier: Optional[Decimal] = 1.00

class FareRuleCreate(FareRuleBase):
    pass

class FareRuleUpdate(BaseModel):
    base_price: Optional[Decimal] = None
    currency: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    peak_hour_multiplier: Optional[Decimal] = None

class FareRule(FareRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FareRuleWithDetails(FareRule):
    line_name: Optional[str] = None
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None
    passenger_type_name: Optional[str] = None

class FareMatrixRow(BaseModel):
    from_station_id: int
    from_station_name: str
    to_station_id: int
    to_station_name: str
    adult_price: Optional[Decimal] = None
    child_price: Optional[Decimal] = None
    senior_price: Optional[Decimal] = None
    member_price: Optional[Decimal] = None

class FareMatrix(BaseModel):
    line_id: int
    line_name: str
    currency: str
    fare_rules: List[FareMatrixRow]

class FareCalculationRequest(BaseModel):
    line_id: int
    from_station_id: int
    to_station_id: int
    passenger_type: str
    travel_time: Optional[datetime] = None

class FareCalculationResponse(BaseModel):
    line_id: int
    from_station_id: int
    to_station_id: int
    passenger_type: str
    base_price: Decimal
    peak_hour_multiplier: Decimal
    final_price: Decimal
    currency: str