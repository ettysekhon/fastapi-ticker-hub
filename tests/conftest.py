import pytest

import app.shared


@pytest.fixture(autouse=True)
def fake_state(monkeypatch):
    prices_store = {}

    class FakeAppState:
        async def get_prices(self):
            return prices_store.copy()

        async def update_prices(self, new_prices):
            nonlocal prices_store
            diffs = {
                sym: data
                for sym, data in new_prices.items()
                if sym not in prices_store or prices_store[sym]["price"] != data["price"]
            }
            prices_store = new_prices.copy()
            return diffs

        async def get_news(self):
            return {}

        async def add_news_item(self, item):
            return "mocked-id"

    monkeypatch.setattr(app.shared, "state", FakeAppState())
    return prices_store
