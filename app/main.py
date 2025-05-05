import asyncio
import json
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis_client
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import app.shared as shared
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # open a single Redis connection and pubsub
    redis = redis_client.from_url(settings.REDIS_URL, decode_responses=True)
    ps = redis.pubsub()
    await ps.subscribe("price-diffs", "news-updates")

    async def reader():
        async for msg in ps.listen():
            if msg["type"] != "message":
                continue
            channel = msg["channel"]
            payload = json.loads(msg["data"])
            # route into the correct room
            if channel == "price-diffs":
                await shared.manager.broadcast("prices", payload)
            else:
                await shared.manager.broadcast("news", payload)

    task = asyncio.create_task(reader())

    yield  # now FastAPI startup is complete

    # shutdown: cancel reader and clean up
    task.cancel()
    await ps.unsubscribe("price-diffs", "news-updates")
    await redis.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def websocket_loop(ws: WebSocket, room: str):
    await shared.manager.connect(ws, room)
    try:
        while True:
            try:
                raw = await ws.receive_text()
            except WebSocketDisconnect:
                break

            try:
                req = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if "watchlist" in req:
                wl = set(req["watchlist"])
                shared.manager.filters[ws] = wl

                current = await shared.state.get_prices()
                filtered = {s: current[s] for s in wl if s in current}
                await ws.send_json(filtered)

    except Exception as e:
        logger.error(f"Error in websocket loop for room={room}: {e}")
    finally:
        await shared.manager.disconnect(ws)


@app.get("/tickers")
async def get_all():
    logger.debug("GET /tickers called")
    return await shared.state.get_prices()


@app.get("/tickers/{symbol}")
async def get_one(symbol: str):
    logger.debug(f"GET /tickers/{symbol} called")
    prices = await shared.state.get_prices()
    if symbol not in prices:
        logger.warning(f"Ticker not found: {symbol}")
        raise HTTPException(status_code=404, detail="Ticker not found")
    return prices[symbol]


@app.websocket("/ws/prices")
async def ws_prices(ws: WebSocket):
    await websocket_loop(ws, "prices")


@app.websocket("/ws/news")
async def ws_news(ws: WebSocket):
    await websocket_loop(ws, "news")
