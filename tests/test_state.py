import pytest
from app import state as state_module
from app.state import state, publish_price_changes

class DummyManager:
    def __init__(self):
        self.calls = []

    async def broadcast(self, room, data):
        # record (room, data) tuples
        self.calls.append((room, data))

@pytest.mark.asyncio
async def test_publish_price_changes(monkeypatch):
    # 1) Seed initial state
    state.prices = {"A": {"price": 1, "ts": 0, "raw": {}}}

    # 2) Swap out the real manager for our dummy
    dummy = DummyManager()
    monkeypatch.setattr(state_module, 'manager', dummy)

    # 3) New fetched prices, A changed, B is new
    new_prices = {
        "A": {"price": 2, "ts": 1, "raw": {}},
        "B": {"price": 3, "ts": 1, "raw": {}},
    }

    # Act
    await publish_price_changes(new_prices)

    # 4) State should have been updated
    assert state.prices == new_prices

    # 5) Exactly one broadcast call
    assert len(dummy.calls) == 1

    room, data = dummy.calls[0]
    # Must broadcast on "prices"
    assert room == "prices"

    # Diffs should include both symbols A and B
    assert set(data.keys()) == {"A", "B"}

@pytest.mark.asyncio
async def test_publish_price_changes_no_diff(monkeypatch):
    # 1) Seed initial state where nothing changes
    state.prices = {"A": {"price": 1, "ts": 0, "raw": {}}}

    dummy = DummyManager()
    monkeypatch.setattr(state_module, 'manager', dummy)

    # 2) New is identical to old
    new_prices = {"A": {"price": 1, "ts": 5, "raw": {}}}

    # Act
    await publish_price_changes(new_prices)

    # State still updates behind the scenes
    assert state.prices == new_prices

    # But no broadcast was called, since price is unchanged
    assert dummy.calls == []
