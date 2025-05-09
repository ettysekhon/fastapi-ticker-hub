import pytest

import app.publisher
from app.publisher import publish_price_changes


class DummyManager:
    def __init__(self):
        self.calls = []

    async def broadcast(self, room, data):
        self.calls.append((room, data))


@pytest.fixture
def fake_state(monkeypatch):
    prices = {}

    class FakeAppState:
        async def update_prices(self, new_prices):
            nonlocal prices
            diffs = {
                sym: data
                for sym, data in new_prices.items()
                if sym not in prices or prices[sym]["price"] != data["price"]
            }
            prices = new_prices.copy()
            return diffs

    monkeypatch.setattr(app.publisher, "state", FakeAppState())
    return prices


@pytest.mark.asyncio
async def test_publish_price_changes(monkeypatch, fake_state):
    dummy = DummyManager()
    monkeypatch.setattr(app.publisher, "manager", dummy)

    new_prices = {
        "A": {"price": 2, "ts": 1, "meta": {}},
        "B": {"price": 3, "ts": 1, "meta": {}},
    }

    await publish_price_changes(new_prices)

    assert len(dummy.calls) == 2
    broadcasted_symbols = {symbol for _, payload in dummy.calls for symbol in payload}
    assert broadcasted_symbols == {"A", "B"}


@pytest.mark.asyncio
async def test_publish_price_changes_no_diff(monkeypatch, fake_state):
    dummy = DummyManager()
    monkeypatch.setattr(app.publisher, "manager", dummy)

    # Populate with existing prices
    fake_state.update({"A": {"price": 1, "ts": 0, "meta": {}}})

    new_prices = {"A": {"price": 1, "ts": 1, "meta": {}}}

    await publish_price_changes(new_prices)
    assert dummy.calls == []
