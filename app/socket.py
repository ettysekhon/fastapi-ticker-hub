import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = {
            "prices": set(),
            "news": set(),
        }
        self.queues: dict[WebSocket, asyncio.Queue] = {}
        self.filters: dict[WebSocket, set[str] | None] = {}
        self.sender_tasks: dict[WebSocket, asyncio.Task] = {}
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, room: str) -> None:
        from .shared import state  # avoid circular import

        if room not in self.rooms:
            logger.warning(f"Attempted to connect to unknown room: {room}")
            return

        await ws.accept()
        async with self.lock:
            self.rooms[room].add(ws)
            self.queues[ws] = asyncio.Queue(maxsize=100)
            self.filters[ws] = None  # None means “send me everything”

        # send initial snapshot (unfiltered)
        snapshot = await state.get_prices() if room == "prices" else await state.get_news()
        await ws.send_json(snapshot)

        # start existing _sender(...)
        self.sender_tasks[ws] = asyncio.create_task(self._sender(ws))

    async def _sender(self, ws: WebSocket):
        queue = self.queues[ws]
        if queue is None:
            logger.warning("No queue found for sender task")
            return
        try:
            while True:
                msg = await queue.get()
                logger.info(f"Sending message to client: {msg}")
                await ws.send_json(msg)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            await self.disconnect(ws)

    async def disconnect(self, ws: WebSocket):
        async with self.lock:
            for room in self.rooms.values():
                room.discard(ws)
            self.queues.pop(ws, None)
            self.filters.pop(ws, None)
            task = self.sender_tasks.pop(ws, None)
            if task:
                task.cancel()
        logger.info("Client fully disconnected")

    async def broadcast(self, room: str, message: dict):
        async with self.lock:
            recipients = list(self.rooms[room])
            if not recipients:
                logger.warning(f"No clients connected to room: {room}")
                return
        for ws in recipients:
            flt = self.filters.get(ws)
            sym = message.get("symbol")
            # if they’ve set a watchlist, skip others
            if flt is not None and sym not in flt:
                continue

            try:
                self.queues[ws].put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("Dropping message for slow client")
                await self.disconnect(ws)
