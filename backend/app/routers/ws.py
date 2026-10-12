from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.db import SessionLocal
from app.models import User
from app.realtime import broadcast, rooms
from app.schemas import MessageIn, MessageOut
from app.security import decode_token
from app.services import tickets as ticket_service

router = APIRouter()


@router.websocket("/ws/tickets/{ticket_id}")
async def ticket_socket(websocket: WebSocket, ticket_id: int, token: str | None = None):
    await websocket.accept()
    raw_token = token or websocket.cookies.get("access_token")
    user_id = decode_token(raw_token, "access") if raw_token else None

    with SessionLocal() as db:
        user = db.get(User, user_id) if user_id else None
        if user is None:
            await websocket.close(code=4401)
            return
        try:
            ticket_service.get_ticket_for_user(db, user, ticket_id)
        except HTTPException:
            await websocket.close(code=4404)
            return

    rooms[ticket_id].add(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except ValueError:
                data = None
            await handle_incoming(websocket, user_id, ticket_id, data)
    except WebSocketDisconnect:
        pass
    finally:
        rooms[ticket_id].discard(websocket)
        if not rooms[ticket_id]:
            del rooms[ticket_id]


async def handle_incoming(websocket: WebSocket, user_id: int, ticket_id: int, data: object) -> None:
    try:
        body = MessageIn.model_validate(data).body
    except ValidationError:
        await websocket.send_json({"type": "error", "message": "Message must be 1-5000 characters"})
        return

    try:
        with SessionLocal() as db:
            user = db.get(User, user_id)
            ticket = ticket_service.get_ticket_for_user(db, user, ticket_id)
            message = ticket_service.add_message(db, user, ticket, body)
            out = MessageOut.model_validate(message).model_dump(mode="json")
    except HTTPException as exc:
        await websocket.send_json({"type": "error", "message": exc.detail})
        return

    await broadcast(ticket_id, {"type": "message", "message": out})
