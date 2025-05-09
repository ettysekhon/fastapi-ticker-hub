import json
import logging
from typing import Any

import redis.asyncio as redis_client

from .config import settings
from .shared import manager, state

logger = logging.getLogger(__name__)


async def publish_price_changes(new_prices: dict[str, dict[str, Any]]) -> None:
    logger.info("Checking for price diffs...")
    diffs = await state.update_prices(new_prices)

    if not diffs:
        logger.info("No price diffs to broadcast.")
        return

    logger.info(f"Broadcasting {len(diffs)} price updates")

    for symbol, data in diffs.items():
        msg = {symbol: data}
        logger.debug("Broadcasting locally: %r", msg)
        await manager.broadcast("prices", msg)

    try:
        redis = redis_client.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
        )
        for symbol, data in diffs.items():
            msg = {symbol: data}
            logger.info(f"Publishing price diff for symbol {symbol}")
            await redis.publish("price-diffs", json.dumps(msg))
    except Exception:
        logger.warning("Failed to publish to Redis; continuing without blocking", exc_info=True)


async def publish_news_update(news_item: dict[str, Any]) -> None:
    key = await state.add_news_item(news_item)
    logger.info(f"Broadcasting news update with key={key}")

    try:
        redis = redis_client.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
        )
        await redis.publish("news-updates", json.dumps(news_item))
    except Exception:
        logger.warning("Failed to publish news to Redis; continuing", exc_info=True)
