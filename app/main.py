import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import app.shared as shared

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

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
                await ws.receive_text()
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Error in websocket loop for room={room}: {e}")
                break
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
