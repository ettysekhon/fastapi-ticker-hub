"""
In-memory state store and change publisher.
Maintains current prices, and broadcasts diffs to WebSocket rooms.
"""
from typing import Dict, Any
from .socket import sio
from .config import settings

# Global state object holding latest prices and optional news
class State:
    def __init__(self):
        # price store: symbol -> { price, ts, raw }
        self.prices: Dict[str, Dict[str, Any]] = {}
        # extendable: news or other data stores
        self.news: Dict[str, Any] = {}

state = State()

async def publish_price_changes(new_prices: Dict[str, Dict[str, Any]]) -> None:
    """
    Compare new_prices against state.prices, update state, and emit diffs to 'prices' room.
    """
    old = state.prices
    diffs: Dict[str, Dict[str, Any]] = {}

    for sym, data in new_prices.items():
        if sym not in old or old[sym]['price'] != data['price']:
            diffs[sym] = data

    # update state
    state.prices = new_prices

    # broadcast diffs if any
    if diffs:
        await sio.emit('update', diffs, room='prices')

async def publish_news_update(news_item: Dict[str, Any]) -> None:
    """
    Add a news item to state.news and emit it to 'news' room.
    """
    # e.g. news_item has an id or timestamp
    key = str(news_item.get('id', len(state.news)))
    state.news[key] = news_item
    await sio.emit('news', news_item, room='news')