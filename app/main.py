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
async def get_all():
    logger.debug("GET /tickers called")
    return await state.get_prices()

@app.get("/tickers/{symbol}")
async def get_one(symbol: str):
    logger.debug(f"GET /tickers/{symbol} called")
    prices = await state.get_prices()
    if symbol not in prices:
        logger.warning(f"Ticker not found: {symbol}")
        raise HTTPException(status_code=404, detail="Ticker not found")
    return prices[symbol]

async def websocket_loop(ws: WebSocket, room: str):
    await manager.connect(ws, room)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)

@app.websocket("/ws/prices")
async def ws_prices(ws: WebSocket):
    await websocket_loop(ws, "prices")

@app.websocket("/ws/news")
async def ws_news(ws: WebSocket):
    await websocket_loop(ws, "news")
