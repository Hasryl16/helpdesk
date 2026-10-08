from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.deps import CurrentUser, CustomerUser, DbSession
from app.realtime import broadcast
from app.schemas import MessageOut, Status, TicketCreateIn, TicketOut, TicketUpdateIn
from app.services import attachments
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
def update_ticket(
    ticket_id: int, data: TicketUpdateIn, user: CurrentUser, db: DbSession, background: BackgroundTasks
):
    if data.status is None and data.assigned_agent_id is None:
        raise HTTPException(422, "Send status or assigned_agent_id")
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    ticket = ticket_service.update_ticket(db, user, ticket, data)
    out = TicketOut.model_validate(ticket)
    # Runs right after the response is sent: everyone viewing the ticket sees the change.
    background.add_task(broadcast, ticket.id, {"type": "ticket", "ticket": out.model_dump(mode="json")})
    return out


@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
def list_messages(ticket_id: int, user: CurrentUser, db: DbSession):
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    return ticket_service.list_messages(db, ticket)


@router.post("/{ticket_id}/attachments", response_model=MessageOut, status_code=201)
def upload_attachment(
    ticket_id: int, file: UploadFile, user: CurrentUser, db: DbSession, background: BackgroundTasks
):
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    ticket_service.ensure_not_closed(ticket)  # check before writing the file to disk
    name = attachments.save_image(file)
    message = ticket_service.add_message(db, user, ticket, attachment_path=name)
    out = MessageOut.model_validate(message)
    background.add_task(broadcast, ticket.id, {"type": "message", "message": out.model_dump(mode="json")})
    return out


@router.get("/{ticket_id}/attachments/{message_id}")
def download_attachment(ticket_id: int, message_id: int, user: CurrentUser, db: DbSession):
    ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
    message = ticket_service.get_attachment_message(db, ticket, message_id)
    path = attachments.file_path(message.attachment_path)
    if not path.is_file():  # e.g. the uploads folder was lost
        raise HTTPException(404, "Attachment not found")
    return FileResponse(path, media_type=attachments.media_type(message.attachment_path))
