import asyncio
from collections import defaultdict

from fastapi import WebSocket

# ticket_id -> sockets currently viewing that ticket.
# ponytail: lives in this process's memory, so run uvicorn with 1 worker; use Redis pub/sub to scale out.
rooms: dict[int, set[WebSocket]] = defaultdict(set)


async def broadcast(ticket_id: int, data: dict) -> None:
    for websocket in list(rooms.get(ticket_id, ())):
        try:
            # A client that stops reading would otherwise block this loop (and everyone after it) forever.
            await asyncio.wait_for(websocket.send_json(data), timeout=5)
        except Exception:  # socket gone or not reading: stop sending to it
            rooms.get(ticket_id, set()).discard(websocket)
