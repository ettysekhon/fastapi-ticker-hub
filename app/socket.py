import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = {
            "prices": set(),
            "news": set(),
        }
        self.queues: dict[WebSocket, asyncio.Queue] = {}
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

        logger.info(f"Client connected to room: {room}")

        # Send initial snapshot
        if room == "prices":
            await ws.send_json(await state.get_prices())
        else:
            await ws.send_json(await state.get_news())

        # Start background sender
        self.sender_tasks[ws] = asyncio.create_task(self._sender(ws))

    async def _sender(self, ws: WebSocket) -> None:
        try:
            queue = self.queues.get(ws)
            if not queue:
                return
            while True:
                message = await queue.get()
                await ws.send_json(message)
        except asyncio.CancelledError:
            # our own cancellation: stop quietly
            return
        except Exception as e:
            logger.warning(f"Sender error for WebSocket: {e}")
        finally:
            await self.disconnect(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self.lock:
            for room in self.rooms.values():
                room.discard(ws)
            self.queues.pop(ws, None)
            task = self.sender_tasks.pop(ws, None)
            if task:
                task.cancel()
        logger.info("Client fully disconnected")

    async def broadcast(self, room: str, message: dict) -> None:
        if room not in self.rooms:
            logger.warning(f"Attempted to broadcast to unknown room: {room}")
            return

        # Copy recipients under lock
        async with self.lock:
            recipients = list(self.rooms[room])

        for ws in recipients:
            queue = self.queues.get(ws)
            if not queue:
                continue

            # Enqueue for the background sender
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("Dropping message for slow client")
                await self.disconnect(ws)
