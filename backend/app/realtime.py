from collections import defaultdict

from fastapi import WebSocket

# ticket_id -> sockets currently viewing that ticket.
# ponytail: lives in this process's memory, so run uvicorn with 1 worker; use Redis pub/sub to scale out.
rooms: dict[int, set[WebSocket]] = defaultdict(set)


async def broadcast(ticket_id: int, data: dict) -> None:
    for websocket in list(rooms.get(ticket_id, ())):
        try:
            await websocket.send_json(data)
        except Exception:  # socket already gone; its own handler removes it from the room
            rooms[ticket_id].discard(websocket)
