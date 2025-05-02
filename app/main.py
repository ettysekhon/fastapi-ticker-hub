import asyncio
import contextlib
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from .socket import app as socket_app
from .state import state
from .polling import poll_loop

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Start background tasks and ensure clean shutdown."""
    logger.info("Starting poll loop")
    poll_task = asyncio.create_task(poll_loop())
    yield
    logger.info("Shutting down poll loop")
    poll_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await poll_task

app = FastAPI(lifespan=lifespan)
# Mount the Socket.IO ASGI app under '/ws'
app.mount("/ws", socket_app)

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