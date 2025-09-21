from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import qrcode
import json
import secrets
import string
from io import BytesIO
import base64

from ..models import Ticket, TicketSegment, PaymentType
from .schemas import (
    BookingRequest, BookingResponse, TicketCreate, TicketWithDetails,
    TicketValidationRequest, TicketValidationResponse, PassengerDetail
)
from ..models import FareRule, PassengerType
from ..fare_rules.service import FareRuleService
from ..models import Station
from ..models import TrainLine

class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_ticket_id(self, length: int = 12) -> str:
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    def generate_qr_code(self, ticket_data: dict) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(ticket_data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode()

    async def create_booking(self, booking_request: BookingRequest, user_id: int) -> BookingResponse:
        fare_service = FareRuleService(self.db)

        # Calculate total fare for all passengers
        total_amount = Decimal('0.00')
        ticket_segments = []
        passenger_details = {}

        # Get passenger types
        passenger_types_query = select(PassengerType)
        passenger_types_result = await self.db.execute(passenger_types_query)
        passenger_types = {pt.name: pt for pt in passenger_types_result.scalars().all()}

        segment_order = 1
        for passenger_detail in booking_request.passengers:
            passenger_type = passenger_types.get(passenger_detail.passenger_type)
            if not passenger_type:
                raise ValueError(f"Invalid passenger type: {passenger_detail.passenger_type}")

            # Calculate fare for this passenger type
            from ..fare_rules.schemas import FareCalculationRequest
            fare_request = FareCalculationRequest(
                line_id=booking_request.line_id,
                from_station_id=booking_request.from_station_id,
                to_station_id=booking_request.to_station_id,
                passenger_type=passenger_detail.passenger_type,
                travel_time=booking_request.travel_datetime
            )

            fare_result = await fare_service.calculate_fare(fare_request)
            if not fare_result:
                raise ValueError(f"No fare rule found for {passenger_detail.passenger_type}")

            # Create ticket segment for each passenger of this type
            for i in range(passenger_detail.count):
                ticket_segments.append({
                    "from_station_id": booking_request.from_station_id,
                    "to_station_id": booking_request.to_station_id,
                    "line_id": booking_request.line_id,
                    "passenger_type_id": passenger_type.id,
                    "fare_amount": fare_result.final_price,
                    "segment_order": segment_order
                })
                total_amount += fare_result.final_price
                segment_order += 1

            # Store passenger details
            passenger_details[passenger_detail.passenger_type] = {
                "count": passenger_detail.count,
                "ages": passenger_detail.ages,
                "unit_price": float(fare_result.final_price)
            }

        # Generate unique ticket ID
        ticket_unique_string = self.generate_ticket_id()
        while await self.ticket_exists(ticket_unique_string):
            ticket_unique_string = self.generate_ticket_id()

        # Set validity period (4 hours from booking)
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(hours=4)

        # Create ticket
        ticket_data = {
            "user_id": user_id,
            "total_amount": total_amount,
            "passenger_details": passenger_details,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "payment_type_id": booking_request.payment_type_id
        }

        db_ticket = Ticket(
            ticket_unique_string=ticket_unique_string,
            **ticket_data
        )

        self.db.add(db_ticket)
        await self.db.flush()

        # Create ticket segments
        for segment_data in ticket_segments:
            segment_data["ticket_id"] = db_ticket.id
            db_segment = TicketSegment(**segment_data)
            self.db.add(db_segment)

        # Generate QR code data
        qr_data = {
            "ticket_id": ticket_unique_string,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
            "total_amount": float(total_amount),
            "passenger_count": sum(pd["count"] for pd in passenger_details.values())
        }

        qr_code_base64 = self.generate_qr_code(qr_data)
        db_ticket.qr_code = qr_code_base64
        db_ticket.status = "active"

        await self.db.commit()
        await self.db.refresh(db_ticket)

        # Get ticket with details for response
        ticket_with_details = await self.get_ticket_with_details(db_ticket.id)

        return BookingResponse(
            ticket=ticket_with_details,
            total_amount=total_amount,
            qr_code_data=qr_code_base64,
            validity_period=f"Valid from {valid_from} to {valid_until} (4 hours)",
            message="Ticket booked successfully"
        )

    async def ticket_exists(self, ticket_unique_string: str) -> bool:
        query = select(Ticket).where(Ticket.ticket_unique_string == ticket_unique_string)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_ticket_with_details(self, ticket_id: int) -> Optional[TicketWithDetails]:
        query = select(Ticket).options(
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.from_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.to_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.line),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.passenger_type),
            selectinload(Ticket.payment_type)
        ).where(Ticket.id == ticket_id)

        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return None

        # Build response with details
        from .schemas import TicketSegmentWithDetails
        segments_with_details = []
        for segment in ticket.ticket_segments:
            segments_with_details.append(TicketSegmentWithDetails(
                id=segment.id,
                ticket_id=segment.ticket_id,
                from_station_id=segment.from_station_id,
                to_station_id=segment.to_station_id,
                line_id=segment.line_id,
                passenger_type_id=segment.passenger_type_id,
                fare_amount=segment.fare_amount,
                segment_order=segment.segment_order,
                status=segment.status,
                created_at=segment.created_at,
                updated_at=segment.updated_at,
                from_station_name=segment.from_station.name,
                to_station_name=segment.to_station.name,
                line_name=segment.line.name,
                passenger_type_name=segment.passenger_type.name
            ))

        return TicketWithDetails(
            id=ticket.id,
            ticket_unique_string=ticket.ticket_unique_string,
            qr_code=ticket.qr_code,
            user_id=ticket.user_id,
            journey_id=ticket.journey_id,
            total_amount=ticket.total_amount,
            paid_currency=ticket.paid_currency,
            paid_amount=ticket.paid_amount,
            passenger_details=ticket.passenger_details,
            status=ticket.status,
            valid_from=ticket.valid_from,
            valid_until=ticket.valid_until,
            issued_at=ticket.issued_at,
            used_at=ticket.used_at,
            payment_type_id=ticket.payment_type_id,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            ticket_segments=segments_with_details,
            payment_type_name=ticket.payment_type.name if ticket.payment_type else None
        )

    async def validate_ticket(self, validation_request: TicketValidationRequest) -> TicketValidationResponse:
        # Find ticket by unique string
        query = select(Ticket).options(
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.from_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.to_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.line),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.passenger_type),
            selectinload(Ticket.payment_type)
        ).where(Ticket.ticket_unique_string == validation_request.ticket_unique_string)

        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return TicketValidationResponse(
                valid=False,
                message="Ticket not found",
                can_use=False
            )

        current_time = datetime.utcnow()

        # Check if ticket is expired
        if current_time > ticket.valid_until:
            return TicketValidationResponse(
                valid=False,
                ticket=await self.get_ticket_with_details(ticket.id),
                message="Ticket has expired",
                can_use=False
            )

        # Check if ticket is not yet valid
        if current_time < ticket.valid_from:
            return TicketValidationResponse(
                valid=False,
                ticket=await self.get_ticket_with_details(ticket.id),
                message="Ticket is not yet valid",
                can_use=False
            )

        # Check if ticket is already used
        if ticket.status == "used":
            return TicketValidationResponse(
                valid=True,
                ticket=await self.get_ticket_with_details(ticket.id),
                message="Ticket has already been used",
                can_use=False
            )

        # Check if ticket is inactive
        if ticket.status != "active":
            return TicketValidationResponse(
                valid=False,
                ticket=await self.get_ticket_with_details(ticket.id),
                message="Ticket is not active",
                can_use=False
            )

        # Ticket is valid and can be used
        return TicketValidationResponse(
            valid=True,
            ticket=await self.get_ticket_with_details(ticket.id),
            message="Ticket is valid and ready to use",
            can_use=True
        )

    async def use_ticket(self, ticket_unique_string: str, station_id: Optional[int] = None) -> bool:
        # Validate ticket first
        validation_request = TicketValidationRequest(
            ticket_unique_string=ticket_unique_string,
            station_id=station_id
        )
        validation_result = await self.validate_ticket(validation_request)

        if not validation_result.can_use:
            return False

        # Mark ticket as used
        current_time = datetime.utcnow()
        update_query = update(Ticket).where(
            Ticket.ticket_unique_string == ticket_unique_string
        ).values(
            status="used",
            used_at=current_time
        )

        await self.db.execute(update_query)
        await self.db.commit()
        return True

    async def get_user_tickets(self, user_id: int, skip: int = 0, limit: int = 100) -> List[TicketWithDetails]:
        query = select(Ticket).options(
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.from_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.to_station),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.line),
            selectinload(Ticket.ticket_segments).selectinload(TicketSegment.passenger_type),
            selectinload(Ticket.payment_type)
        ).where(Ticket.user_id == user_id).offset(skip).limit(limit).order_by(Ticket.created_at.desc())

        result = await self.db.execute(query)
        tickets = result.scalars().all()

        tickets_with_details = []
        for ticket in tickets:
            ticket_details = await self.get_ticket_with_details(ticket.id)
            if ticket_details:
                tickets_with_details.append(ticket_details)

        return tickets_with_details