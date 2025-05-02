from typing import Dict, Any
from .socket import manager
import logging

logger = logging.getLogger(__name__)

class State:
    def __init__(self):
        self.prices: Dict[str, Dict[str, Any]] = {}
        self.news: Dict[str, Any] = {}

state = State()

async def publish_price_changes(new_prices: Dict[str, Dict[str, Any]]) -> None:
    """
    Compare new_prices against state.prices, update state, and broadcast diffs to 'prices' channel.
    """
    logger.info("Publishing price changes, checking for diffs...")
    old = state.prices
    diffs: Dict[str, Dict[str, Any]] = {}

    for sym, data in new_prices.items():
        if sym not in old or old[sym]['price'] != data['price']:
            diffs[sym] = data

    state.prices = new_prices

    if diffs:
        logger.info(f"Price diffs to broadcast: {diffs!r}")
        await manager.broadcast('prices', diffs)
    else:
        logger.info("No price diffs detected.")

async def publish_news_update(news_item: Dict[str, Any]) -> None:
    """
    Add a news item to state.news and broadcast it to 'news' channel.
    """
    key = str(news_item.get('id', len(state.news)))
    state.news[key] = news_item
    logger.info(f"Publishing news update: {news_item}")
    await manager.broadcast('news', news_item)
