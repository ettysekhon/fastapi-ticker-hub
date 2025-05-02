import asyncio
import time
import logging
from typing import Dict, Any
import yfinance as yf
from fastapi.concurrency import run_in_threadpool
from .config import settings
from .state import publish_price_changes

logger = logging.getLogger(__name__)

async def poll_loop():
    """
    Fetch prices at regular intervals and publish any diffs.
    Uses `fetch_prices` to retrieve data via yfinance in a threadpool.
    """
    backoff = settings.POLL_FREQ
    while True:
        try:
            new_prices = await fetch_prices(settings.TICKERS)
            if not new_prices:
                logger.warning("No prices fetched")
            logger.debug(f"Fetched prices: {new_prices}")
            await publish_price_changes(new_prices)
            logger.info("Publishing price changes")
            backoff = settings.POLL_FREQ
        except Exception as e:
            logger.error(f"Polling error: {e}")
        await asyncio.sleep(backoff)

async def fetch_prices(tickers: list[str]) -> Dict[str, Dict[str, Any]]:
    """
    Synchronously fetches prices using yfinance in an async-compatible way.
    Returns { symbol: { price, ts, raw } }.
    """
    if not tickers:
        return {}

    def sync_fetch() -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)
                price = t.fast_info.last_price if hasattr(t, 'fast_info') else t.info.get('regularMarketPrice')
                ts = int(time.time())
                raw = t.info
                results[symbol] = {"price": price, "ts": ts, "raw": raw}
                logger.debug(f"Fetched {symbol}: {price} at {ts}")
            except Exception as err:
                logger.warning(f"Error fetching {symbol}: {err}")
        return results

    # run blocking sync_fetch in threadpool
    return await run_in_threadpool(sync_fetch)