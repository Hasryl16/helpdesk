from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Message, Ticket, User, utcnow
from app.schemas import TicketCreateIn, TicketUpdateIn

# Which status may follow which. "resolved" -> "open" is the reopen path.
ALLOWED_TRANSITIONS = {
    "open": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"closed", "open"},
    "closed": set(),
}


def visible_tickets(user: User) -> Select:
    """Tickets this user may see. Every ticket read starts from this query."""
    query = select(Ticket).where(Ticket.business_id == user.business_id)
    if user.role == "customer":
        query = query.where(Ticket.customer_id == user.id)
    return query


def get_ticket_for_user(db: Session, user: User, ticket_id: int) -> Ticket:
    # A ticket of another business (or customer) looks exactly like a missing one: 404.
    ticket = db.scalar(visible_tickets(user).where(Ticket.id == ticket_id))
    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    return ticket


def list_tickets(db: Session, user: User, status: str | None) -> list[Ticket]:
    query = visible_tickets(user).order_by(Ticket.updated_at.desc(), Ticket.id.desc())
    if status:
        query = query.where(Ticket.status == status)
    return list(db.scalars(query))


def create_ticket(db: Session, customer: User, data: TicketCreateIn) -> Ticket:
    ticket = Ticket(
        business_id=customer.business_id,
        customer_id=customer.id,
        subject=data.subject,
        category=data.category,
        priority=data.priority,
    )
    db.add(ticket)
    db.flush()  # gives ticket.id so the first message can point to it
    db.add(Message(ticket_id=ticket.id, sender_id=customer.id, body=data.message))
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, user: User, ticket: Ticket, data: TicketUpdateIn) -> Ticket:
    if user.role == "customer" and (data.assigned_agent_id is not None or data.status != "open"):
        raise HTTPException(403, "Customers can only reopen a resolved ticket")

    if data.assigned_agent_id is not None:
        if user.role == "agent" and data.assigned_agent_id != user.id:
            raise HTTPException(403, "Agents can only assign tickets to themselves")
        agent = db.scalar(
            select(User).where(
                User.id == data.assigned_agent_id,
                User.business_id == user.business_id,
                User.role == "agent",
            )
        )
        if agent is None:
            raise HTTPException(404, "Agent not found")
        ticket.assigned_agent = agent
        if ticket.status == "open":
            ticket.status = "in_progress"

    if data.status is not None:
        if data.status not in ALLOWED_TRANSITIONS[ticket.status]:
            raise HTTPException(409, f"Cannot change status from {ticket.status} to {data.status}")
        ticket.status = data.status

    ticket.updated_at = utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def list_messages(db: Session, ticket: Ticket) -> list[Message]:
    query = select(Message).where(Message.ticket_id == ticket.id).order_by(Message.created_at, Message.id)
    return list(db.scalars(query))
