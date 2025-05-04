import logging
from typing import Any

from .shared import manager, state

logger = logging.getLogger(__name__)


async def publish_price_changes(new_prices: dict[str, dict[str, Any]]) -> None:
    logger.info("Checking for price diffs...")
    diffs = await state.update_prices(new_prices)

    if diffs:
        logger.info(f"Broadcasting {len(diffs)} price updates")
        for symbol, data in diffs.items():
            await manager.broadcast("prices", {"symbol": symbol, **data})
    else:
        logger.info("No price diffs to broadcast.")


async def publish_news_update(news_item: dict[str, Any]) -> None:
    key = await state.add_news_item(news_item)
    logger.info(f"Broadcasting news update with key={key}")
    await manager.broadcast("news", news_item)
