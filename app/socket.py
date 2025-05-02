from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, set[WebSocket]] = {"prices": set(), "news": set()}

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self.rooms[room].add(ws)
        if room == "prices":
            from .state import state
            logger.info("Sending initial prices snapshot to new client")
            await ws.send_json(state.prices)
        elif room == "news":
            from .state import state
            logger.info("Sending initial news snapshot to new client")
            await ws.send_json(state.news)

    def disconnect(self, ws: WebSocket):
        for room in self.rooms:
            self.rooms[room].discard(ws)

    async def broadcast(self, room: str, message: dict):
        for ws in list(self.rooms.get(room, ())):
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("Dropping broken WS connection")
                self.disconnect(ws)
# single shared manager
manager = ConnectionManager()