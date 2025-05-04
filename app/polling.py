import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import yfinance as yf
from fastapi.concurrency import run_in_threadpool

from .config import settings
from .publisher import publish_price_changes

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


def slim_info(info: dict[str, Any]) -> dict[str, Any]:
    """Pick just the fields we need based on quoteType."""
    out: dict[str, Any] = {}
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
    logger.info(f"Started polling loop in task: {asyncio.current_task().get_name()}")
    while True:
        try:
            new_prices = await fetch_prices(settings.tickers_list)
            if not new_prices:
                logger.warning("No prices fetched")
            logger.debug(f"Fetched prices: {new_prices}")
            await publish_price_changes(new_prices)
            backoff = settings.POLL_FREQ  # reset backoff after success
        except Exception:
            logger.exception("Unexpected error during polling")
            backoff = min(backoff * 2, 60)  # simple exponential backoff
        await asyncio.sleep(backoff)


async def fetch_prices(tickers: list[str]) -> dict[str, dict[str, Any]]:
    """
    Synchronously fetches prices using yfinance in an async-compatible way.
    Returns { symbol: { price, ts, meta } }.
    """
    tickers = list(set(tickers))  # deduplicate
    if not tickers:
        logger.warning("Empty ticker list passed to fetch_prices()")
        return {}

    def sync_fetch() -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        now_utc = datetime.now(UTC).replace(microsecond=0)
        now_iso = now_utc.isoformat() + "Z"

        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)  # consider caching if fetching many tickers at high frequency
                info = t.info or {}
                meta = slim_info(info)
                price = meta.get("price")

                market_epoch = info.get("regularMarketTime", int(time.time()))
                market_dt = datetime.fromtimestamp(market_epoch, tz=UTC).replace(microsecond=0)
                market_iso = market_dt.isoformat().replace("+00:00", "Z")

                results[symbol] = {
                    "price": price,
                    "marketTime": market_iso,
                    "publishedTime": now_iso,
                    "meta": meta,
                }
                logger.debug(f"Fetched {symbol}: {price} at {now_iso}")
            except Exception as err:
                logger.warning(f"Error fetching {symbol}: {err}")
        return results

    return await run_in_threadpool(sync_fetch)
