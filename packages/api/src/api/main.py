import asyncio
import json
import logging
from datetime import UTC

import redis.asyncio as aioredis
import yfinance as yf

# https://github.com/ranaroussi/yfinance/issues/2422
from curl_cffi import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import ConnectionError as RedisConnectionError

from .schemas import OHLCVPoint
from .settings import REDIS_URL
from .state import get_prices

session = requests.Session(impersonate="chrome")

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

redis = aioredis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
)
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


@app.get("/tickers/{symbol}/history", response_model=list[OHLCVPoint])
async def history(symbol: str, start: str, end: str):
    def fetch():
        df = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            session=session,
        )
        if df.empty:
            raise HTTPException(404, f"No data for {symbol}")

        if df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
        else:
            df.index = df.index.tz_convert(UTC)

        out: list[OHLCVPoint] = []
        for ts, row in df.iterrows():
            out.append(
                {
                    "date": ts.isoformat().replace("+00:00", "Z"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )
        return out

    return await asyncio.to_thread(fetch)


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
        while True:
            try:
                async for msg in pubsub.listen():
                    if msg.get("type") != "message":
                        continue
                    data = json.loads(msg["data"])
                    await ws.send_json(data)
                break

            except (RedisConnectionError, OSError) as err:
                logger.warning("Redis PubSub dropped, reconnecting…", exc_info=err)
                try:
                    await pubsub.unsubscribe(CHANNEL)
                    await pubsub.close()
                except Exception:
                    pass
                pubsub = redis.pubsub()
                await pubsub.subscribe(CHANNEL)
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

    finally:
        try:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.close()
        except Exception:
            pass
        logger.info("Cleaned up Redis subscription")
