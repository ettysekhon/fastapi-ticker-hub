import asyncio
import logging
from typing import Dict, Any
from .socket import manager

logger = logging.getLogger(__name__)

class State:
    def __init__(self):
        self.prices: Dict[str, Dict[str, Any]] = {}
        self.news: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get_prices(self) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            return self.prices.copy()

    async def update_prices(self, new_prices: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            diffs = {
                sym: data for sym, data in new_prices.items()
                if sym not in self.prices or self.prices[sym]['price'] != data['price']
            }
            self.prices = new_prices
            return diffs

    async def add_news_item(self, item: Dict[str, Any]) -> str:
        async with self._lock:
            key = str(item.get("id", len(self.news)))
            self.news[key] = item
            return key

    async def get_news(self) -> Dict[str, Any]:
        async with self._lock:
            return self.news.copy()

# Shared instance
state = State()

async def publish_price_changes(new_prices: Dict[str, Dict[str, Any]]) -> None:
    logger.info("Checking for price diffs...")
    diffs = await state.update_prices(new_prices)

    if diffs:
        logger.info(f"Broadcasting {len(diffs)} price updates")
        await manager.broadcast("prices", diffs)
    else:
        logger.info("No price diffs to broadcast.")

async def publish_news_update(news_item: Dict[str, Any]) -> None:
    key = await state.add_news_item(news_item)
    logger.info(f"Broadcasting news update with key={key}")
    await manager.broadcast("news", news_item)
