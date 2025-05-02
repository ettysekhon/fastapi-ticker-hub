import asyncio
import contextlib
import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .state import state
from .polling import poll_loop
from .socket import manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting poll loop")
    task = asyncio.create_task(poll_loop())
    yield
    logger.info("Shutting down poll loop")
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tickers")
def get_all():
    logger.debug("GET /tickers called")
    return state.prices

@app.get("/tickers/{symbol}")
def get_one(symbol: str):
    logger.debug(f"GET /tickers/{symbol} called")
    if symbol not in state.prices:
        logger.warning(f"Ticker not found: {symbol}")
        raise HTTPException(status_code=404, detail="Ticker not found")
    return state.prices[symbol]

async def _ws_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        # keep the connection open indefinitely
        while True:
            await asyncio.sleep(3600)
    except Exception:
        pass
    finally:
        manager.disconnect(websocket, room)

@app.websocket("/ws/prices")
async def ws_prices(ws: WebSocket):
    await manager.connect(ws, "prices")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.websocket("/ws/news")
async def ws_news(ws: WebSocket):
    await manager.connect(ws, "news")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)