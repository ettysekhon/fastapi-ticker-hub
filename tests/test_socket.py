import pytest
import asyncio
from app.socket import ConnectionManager
from app.state import state

class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        # Record exactly what was sent
        self.sent.append(payload)

@pytest.mark.asyncio
async def test_connect_sends_initial_snapshot_and_registers():
    # Arrange
    cm = ConnectionManager()
    ws = DummyWebSocket()
    # Seed the global state with some prices
    state.prices = {"FOO": {"price": 1, "ts": 0, "raw": {}}}
    # Act
    await cm.connect(ws, "prices")
    # Assert
    assert ws.accepted, "WebSocket.accept() was not called"
    assert ws in cm.rooms["prices"], "WebSocket was not registered in 'prices' room"
    # The first message should be the full snapshot
    assert ws.sent == [state.prices]

@pytest.mark.asyncio
async def test_broadcast_to_all_clients_and_cleanup_on_error(monkeypatch):
    # Arrange
    cm = ConnectionManager()
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()
    # Register them in the "prices" room
    await cm.connect(ws1, "prices")
    await cm.connect(ws2, "prices")
    # Now monkey‐patch ws2.send_json to raise, simulating a broken socket
    async def broken_send(_):
        raise RuntimeError("send failed")
    ws2.send_json = broken_send

    # Act: broadcast a diff
    message = {"FOO": {"price": 2, "ts": 1, "raw": {}}}
    await cm.broadcast("prices", message)

    # Assert: ws1 got the message
    assert ws1.sent == [state.prices, message]
    # ws2 threw, so it should be removed
    assert ws2 not in cm.rooms["prices"], "Broken WebSocket should be pruned on error"

@pytest.mark.asyncio
async def test_disconnect_removes_websocket_from_all_rooms():
    cm = ConnectionManager()
    ws = DummyWebSocket()
    # Manually put ws into both rooms
    cm.rooms["prices"].add(ws)
    cm.rooms["news"].add(ws)

    # Act
    cm.disconnect(ws)

    # Assert
    assert ws not in cm.rooms["prices"]
    assert ws not in cm.rooms["news"]
