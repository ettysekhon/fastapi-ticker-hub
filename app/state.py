import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class AppState:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get_prices(self) -> dict[str, dict[str, Any]]:
        raw = await self.redis.get("prices")
        return json.loads(raw) if raw else {}

    async def update_prices(
        self, new_prices: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        old_prices = await self.get_prices()
        diffs = {
            sym: data
            for sym, data in new_prices.items()
            if sym not in old_prices or old_prices[sym]["price"] != data["price"]
        }
        await self.redis.set("prices", json.dumps(new_prices))
        return diffs

    async def add_news_item(self, item: dict[str, Any]) -> str:
        key = str(item.get("id")) or await self.redis.incr("news:counter")
        await self.redis.hset("news", key, json.dumps(item))
        return key

    async def get_news(self) -> dict[str, Any]:
        raw_items = await self.redis.hgetall("news")
        return {k: json.loads(v) for k, v in raw_items.items()}
