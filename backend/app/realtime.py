import asyncio
from collections import defaultdict

from fastapi import WebSocket

rooms: dict[int, set[WebSocket]] = defaultdict(set)


async def broadcast(ticket_id: int, data: dict) -> None:
    for websocket in list(rooms.get(ticket_id, ())):
        try:
            await asyncio.wait_for(websocket.send_json(data), timeout=5)
        except Exception:
            rooms.get(ticket_id, set()).discard(websocket)
