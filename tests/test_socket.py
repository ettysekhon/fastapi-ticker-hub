import pytest
from app.socket import sio, subscribe

@pytest.mark.asyncio
async def test_subscribe_room(monkeypatch):
    """Test that the subscribe event calls enter_room with correct args."""
    sid = 'testsid'
    calls = []
    # Stub out enter_room to capture its parameters
    async def mock_enter_room(s, room):
        calls.append((s, room))
    monkeypatch.setattr(sio, 'enter_room', mock_enter_room)

    # Invoke the subscribe handler
    await subscribe(sid, {'room': 'prices'})

    # Assert enter_room was called with our sid and room
    assert calls == [(sid, 'prices')]