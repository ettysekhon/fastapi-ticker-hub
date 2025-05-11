# services/api/src/api/state.py

import json
import logging

import redis.asyncio as redis_client

from .settings import REDIS_URL

logger = logging.getLogger(__name__)

# single Redis client
_redis = redis_client.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
)


async def get_prices() -> dict[str, dict]:
    """
    Fetch the full latest 'prices' snapshot from Redis.
    On any error, log and return empty dict.
    """
    try:
        raw = await _redis.get("prices")
    except Exception as e:
        logger.warning("Redis get_prices failed, returning empty snapshot", exc_info=e)
        return {}
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        logger.warning("Corrupt JSON in 'prices' key, returning empty snapshot")
        return {}
