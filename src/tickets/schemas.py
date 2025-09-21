from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class PassengerDetail(BaseModel):
    passenger_type: str
    count: int
    ages: Optional[List[int]] = []

class TicketSegmentBase(BaseModel):
    from_station_id: int
    to_station_id: int
    line_id: int
    passenger_type_id: int
    fare_amount: Decimal
    segment_order: int

class TicketSegmentCreate(TicketSegmentBase):
    pass

class TicketSegment(TicketSegmentBase):
    id: int
    ticket_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketSegmentWithDetails(TicketSegment):
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None
    line_name: Optional[str] = None
    passenger_type_name: Optional[str] = None

class BookingRequest(BaseModel):
    from_station_id: int
    to_station_id: int
    line_id: int
    passengers: List[PassengerDetail]
    travel_datetime: Optional[datetime] = None
    payment_type_id: Optional[int] = None

class TicketBase(BaseModel):
    user_id: int
    journey_id: Optional[int] = None
    total_amount: Decimal
    paid_currency: str = "THB"
    paid_amount: Optional[Decimal] = None
    passenger_details: Optional[Dict[str, Any]] = None
    valid_from: datetime
    valid_until: datetime
    payment_type_id: Optional[int] = None

class TicketCreate(TicketBase):
    ticket_segments: List[TicketSegmentCreate]

class Ticket(TicketBase):
    id: int
    ticket_unique_string: str
    qr_code: Optional[str] = None
    status: str
    issued_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketWithDetails(Ticket):
    ticket_segments: List[TicketSegmentWithDetails] = []
    payment_type_name: Optional[str] = None

class TicketValidationRequest(BaseModel):
    ticket_unique_string: str
    station_id: Optional[int] = None

class TicketValidationResponse(BaseModel):
    valid: bool
    ticket: Optional[TicketWithDetails] = None
    message: str
    can_use: bool = False

class PaymentTypeBase(BaseModel):
    name: str
    code: str
    status: str = "active"
    processing_fee: Decimal = 0.00

class PaymentTypeCreate(PaymentTypeBase):
    pass

class PaymentType(PaymentTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    ticket: TicketWithDetails
    total_amount: Decimal
    qr_code_data: str
    validity_period: str
    message: str