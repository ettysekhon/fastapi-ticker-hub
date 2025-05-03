import asyncio
import time
import logging
from typing import Dict, Any
import yfinance as yf
from fastapi.concurrency import run_in_threadpool
from .config import settings
from .state import publish_price_changes
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

COMMON = {
    "symbol": "symbol",
    "name": "shortName",
    "currency": "currency",
    "price": "regularMarketPrice",
    "change": "regularMarketChange",
    "changePercent": "regularMarketChangePercent",
    "marketState": "marketState",
}

FUTURES_EXTRA = {
    "expiry": "expireIsoDate",
    "underlying": "underlyingSymbol",
    "openInterest": "openInterest",
}

OPTIONS_EXTRA = {
    "strike": "strike",
    "expiry": "expireIsoDate",
    "optionType": "optionType",
}

def slim_info(info: Dict[str, Any]) -> Dict[str, Any]:
    """Pick just the fields we need based on quoteType."""
    out: Dict[str, Any] = {}
    
    for out_key, info_key in COMMON.items():
        out[out_key] = info.get(info_key)
    qtype = info.get("quoteType", "").lower()
    if qtype == "future":
        for out_key, info_key in FUTURES_EXTRA.items():
            out[out_key] = info.get(info_key)
    elif qtype == "option":
        for out_key, info_key in OPTIONS_EXTRA.items():
            out[out_key] = info.get(info_key)
    return out

async def poll_loop():
    """
    Fetch prices at regular intervals and publish any diffs.
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
    Returns { symbol: { price, ts, meta } }.
    """
    if not tickers:
        return {}

    def sync_fetch() -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
        
        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)
                info = t.info or {}
                meta = slim_info(info)
                price = meta.get("price")

                market_epoch = info["regularMarketTime"]
                if not market_epoch:
                    logger.warning(f"No market time for {symbol}")
                    market_epoch = int(time.time())
                market_dt = datetime.fromtimestamp(market_epoch, tz=timezone.utc).replace(microsecond=0)
                market_iso = market_dt.isoformat().replace("+00:00", "Z")

                pub_dt = datetime.now(timezone.utc).replace(microsecond=0)
                pub_iso = pub_dt.isoformat().replace("+00:00", "Z")

                results[symbol] = {
                    "price": price,
                    "marketTime": market_iso,
                    "publishedTime": pub_iso,
                    "meta": meta
                }
                logger.debug(f"Fetched {symbol}: {price} at {now_iso}")
            except Exception as err:
                logger.warning(f"Error fetching {symbol}: {err}")
        return results

    # run blocking sync_fetch in threadpool
    return await run_in_threadpool(sync_fetch)
