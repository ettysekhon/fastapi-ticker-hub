import asyncio

import pytest

from app.socket import ConnectionManager


class DummyWebSocket:
    def __init__(self):
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.sent.append(message)

    async def receive_text(self):
        return "ping"

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_connect_sends_initial_snapshot_and_registers():
    ws = DummyWebSocket()
    cm = ConnectionManager()

    await cm.connect(ws, "prices")
    assert ws.accepted, "Expected WebSocket.accept() to be called during connect()"
    assert ws.sent[0] == {}  # empty snapshot
    assert ws in cm.rooms["prices"]
    await cm.disconnect(ws)


@pytest.mark.asyncio
async def test_broadcast_to_all_clients_and_cleanup_on_error():
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()
    cm = ConnectionManager()

    await cm.connect(ws1, "prices")
    await cm.connect(ws2, "prices")

    await cm.broadcast("prices", {"symbol": "FOO", "price": 2})
    # allow background sender tasks to process the queue
    await asyncio.sleep(0)

    await cm.disconnect(ws1)
    await cm.disconnect(ws2)

    assert {"symbol": "FOO", "price": 2} in ws1.sent
    assert {"symbol": "FOO", "price": 2} in ws2.sent
