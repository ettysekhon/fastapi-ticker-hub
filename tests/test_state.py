import pytest
from app.state import state, publish_price_changes

class DummySio:
    def __init__(self):
        self.events = []
    async def emit(self, event, data, room=None):
        self.events.append((event, data, room))

@pytest.mark.asyncio
async def test_publish_price_changes(monkeypatch):
    state.prices = {"A": {"price": 1, "ts": 0, "raw": {}}}
    dummy = DummySio()
    monkeypatch.setattr("app.state.sio", dummy)

    new = {
        "A": {"price": 2, "ts": 1, "raw": {}},
        "B": {"price": 3, "ts": 1, "raw": {}}
    }
    await publish_price_changes(new)

    # Ensure at least one emit to the 'prices' room
    assert any(evt[2] == "prices" for evt in dummy.events)
    # Ensure diffs contain both A and B
    assert "A" in dummy.events[0][1] and "B" in dummy.events[0][1]
