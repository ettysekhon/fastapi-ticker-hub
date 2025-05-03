import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {
            "prices": set(),
            "news": set(),
        }
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, room: str) -> None:
        if room not in self.rooms:
            logger.warning(f"Attempted to connect to unknown room: {room}")
            return

        await ws.accept()

        async with self.lock:
            self.rooms[room].add(ws)

        logger.info(f"Client connected to room: {room}")

# Defer import to avoid circular dependency (ideally restructure)
        from .state import state
        if room == "prices":
            logger.info("Sending initial prices snapshot to new client")
            await ws.send_json(state.prices)
        elif room == "news":
            logger.info("Sending initial news snapshot to new client")
            await ws.send_json(state.news)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self.lock:
            for room in self.rooms:
                if ws in self.rooms[room]:
                    self.rooms[room].remove(ws)
                    logger.info(f"Client disconnected from room: {room}")

    async def broadcast(self, room: str, message: dict) -> None:
        if room not in self.rooms:
            logger.warning(f"Attempted to broadcast to unknown room: {room}")
            return

        async with self.lock:
            websockets = list(self.rooms[room])  # Copy to avoid mutation during iteration

        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Dropping broken WS connection: {e}")
                await self.disconnect(ws)

# Shared singleton instance
manager = ConnectionManager()
