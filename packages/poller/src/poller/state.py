import json
import logging
from typing import Any

import redis.asyncio as aioredis

from .settings import REDIS_URL

logger = logging.getLogger(__name__)
_redis = aioredis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
)

# In-memory cache of the full snapshot
_snapshot: dict[str, dict[str, Any]] = {}


async def update_prices(new_prices: dict[str, dict[str, Any]]) -> None:
    """
    Merge only the incoming ticker(s) into our in-memory snapshot,
    then overwrite the 'prices' key in Redis with the full JSON.
    """
    _snapshot.update(new_prices)

    try:
        await _redis.set("prices", json.dumps(_snapshot))
    except Exception:
        logger.exception("Failed to write full snapshot to Redis")
