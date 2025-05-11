# services/poller/src/poller/main.py

import asyncio
import json
import logging
import random
import time
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
import yfinance as yf

from .settings import POLL_FREQ, REDIS_URL, tickers_list
from .state import update_prices  # <— import our helper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MAX_BACKOFF = 36000

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


async def poll_one(ticker: str, redis_client: aioredis.Redis):
    backoff = POLL_FREQ
    last_price: float | None = None

    logger.info(f"Polling {ticker!r} every {POLL_FREQ}s (diff mode)")

    while True:
        try:
            info = await asyncio.to_thread(lambda: yf.Ticker(ticker).info)
            meta = slim_info(info)
            price = meta.get("price")

            if price is None:
                logger.warning(f"No price for {ticker!r}")
            else:
                if last_price is None or price != last_price:
                    now_utc = datetime.now(UTC).replace(microsecond=0)
                    fetched_at = now_utc.isoformat().replace("+00:00", "Z")

                    market_epoch = info.get("regularMarketTime", int(time.time()))
                    market_dt = datetime.fromtimestamp(market_epoch, tz=UTC).replace(microsecond=0)
                    market_time = market_dt.isoformat().replace("+00:00", "Z")

                    payload = {
                        ticker: {
                            "price": price,
                            "marketTime": market_time,
                            "fetchedAt": fetched_at,
                            "meta": meta,
                        }
                    }

                    logger.info(
                        f"Price change detected for {ticker!r}: {last_price!r} → {price!r}, publishing"
                    )
                    await update_prices(payload)
                    await redis_client.publish("price-diffs", json.dumps(payload))
                    last_price = price
                else:
                    logger.debug(f"No change for {ticker!r} ({price!r}); skipping publish")

            backoff = POLL_FREQ

        except asyncio.CancelledError:
            logger.info(f"Cancelled poll task for {ticker!r}")
            break

        except Exception:
            logger.exception(f"Error polling {ticker!r}, backing off {backoff}s")
            backoff = min(backoff * 2, MAX_BACKOFF)
            backoff = random.uniform(backoff / 2, backoff)

        await asyncio.sleep(backoff)


async def main():
    tickers = tickers_list()
    if not tickers:
        logger.error("No tickers configured; set TICKERS env var")
        return

    redis_client = aioredis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_keepalive=True,
        health_check_interval=30,
    )

    logger.info(f"Starting diff-based poller for {tickers} every {POLL_FREQ}s")
    tasks = [asyncio.create_task(poll_one(sym, redis_client)) for sym in tickers]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Shutdown requested, cancelling all poll tasks")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
