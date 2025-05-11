import json
import logging

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .settings import REDIS_URL
from .state import get_prices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = aioredis.from_url(REDIS_URL, decode_responses=True)
CHANNEL = "price-diffs"


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/tickers")
async def all_tickers():
    """Return the full latest snapshot of all prices."""
    return await get_prices()


@app.get("/tickers/{symbol}")
async def one_ticker(symbol: str):
    """Return the latest price for a single symbol, or 404 if not found."""
    prices = await get_prices()
    if symbol not in prices:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return prices[symbol]


@app.websocket("/ws/prices")
async def websocket_prices(ws: WebSocket):
    """WebSocket streaming of price-diffs as they arrive, with initial snapshot."""
    await ws.accept()

    snapshot = await get_prices()
    if snapshot:
        await ws.send_json(snapshot)

    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL)
    logger.info(f"WebSocket client connected, subscribed to {CHANNEL}")

    try:
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            data = json.loads(msg["data"])
            await ws.send_json(data)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

    finally:
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.close()
        logger.info("Cleaned up Redis subscription")
