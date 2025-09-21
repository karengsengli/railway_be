from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..auth.dependencies import get_current_user
from .service import TicketService
from .schemas import (
    BookingRequest, BookingResponse, TicketWithDetails,
    TicketValidationRequest, TicketValidationResponse
)

router = APIRouter()

@router.post("/book", response_model=BookingResponse)
async def book_ticket(
    booking_request: BookingRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = TicketService(db)
    try:
        return await service.create_booking(booking_request, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create booking")

@router.post("/validate", response_model=TicketValidationResponse)
async def validate_ticket(
    validation_request: TicketValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    service = TicketService(db)
    return await service.validate_ticket(validation_request)

@router.post("/use/{ticket_unique_string}")
async def use_ticket(
    ticket_unique_string: str,
    station_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    service = TicketService(db)
    success = await service.use_ticket(ticket_unique_string, station_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot use this ticket")
    return {"message": "Ticket used successfully"}

@router.get("/my-tickets", response_model=List[TicketWithDetails])
async def get_my_tickets(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = TicketService(db)
    return await service.get_user_tickets(current_user.id, skip, limit)

@router.get("/{ticket_id}", response_model=TicketWithDetails)
async def get_ticket(
    ticket_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = TicketService(db)
    ticket = await service.get_ticket_with_details(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check if user owns the ticket or is admin
    if ticket.user_id != current_user.id:
        # TODO: Add admin role check here
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    return ticket