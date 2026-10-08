from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, CustomerUser, DbSession
from app.schemas import MessageOut, Status, TicketCreateIn, TicketOut, TicketUpdateIn
from app.services import tickets as ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
def list_tickets(user: CurrentUser, db: DbSession, status: Status | None = None):
    return ticket_service.list_tickets(db, user, status)


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketCreateIn, customer: CustomerUser, db: DbSession):
    return ticket_service.create_ticket(db, customer, data)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, user: CurrentUser, db: DbSession):
    return ticket_service.get_ticket_for_user(db, user, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdateIn, user: CurrentUser, db: DbSession):
    if data.status is None and data.assigned_agent_id is None:
        raise HTTPException(422, "Send status or assigned_agent_id")
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    return ticket_service.update_ticket(db, user, ticket, data)


@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
def list_messages(ticket_id: int, user: CurrentUser, db: DbSession):
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    return ticket_service.list_messages(db, ticket)
