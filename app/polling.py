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
    backoff = settings.POLL_FREQ
    while True:
        try:
            new_prices = await fetch_prices(settings.TICKERS)
            if new_prices:
                await publish_price_changes(new_prices)
            else:
                logger.warning('No prices fetched')
            backoff = settings.POLL_FREQ
        except Exception as e:
            logger.error(f'Polling error: {e}')
        await asyncio.sleep(backoff)

async def fetch_prices(tickers: list[str]) -> Dict[str, Dict[str, Any]]:
    if not tickers:
        return {}

    def sync_fetch() -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)
                price = getattr(t.fast_info, 'last_price', t.info.get('regularMarketPrice'))
                ts = int(time.time())
                raw = t.info
                results[symbol] = {"price": price, "ts": ts, "raw": raw}
            except Exception as err:
                logger.warning(f'Error fetching {symbol}: {err}')
        return results

    return await run_in_threadpool(sync_fetch)