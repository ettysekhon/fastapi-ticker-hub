import socketio
import os
from fastapi import FastAPI
from .config import settings

# Choose Redis manager if URL provided
manager = None
if settings.REDIS_URL:
    manager = socketio.AsyncRedisManager(settings.REDIS_URL)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=manager,
    cors_allowed_origins="*"
)

# Mount on FastAPI
app = FastAPI()
app.mount("/ws", socketio.ASGIApp(sio, other_asgi_app=app))

@sio.event
async def subscribe(sid, data):
    """Join a room, e.g. 'prices' or 'news'."""
    room = data.get("room")
    await sio.enter_room(sid, room)

@sio.event
async def disconnect(sid):
    """Cleanup on disconnect: leave all rooms the client joined."""
    # Get all rooms this SID is in (including its own default room)
    rooms = list(sio.rooms(sid))
    for room in rooms:
        await sio.leave_room(sid, room)