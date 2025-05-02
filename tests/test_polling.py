import asyncio
import pytest
from app.polling import fetch_prices, poll_loop
from app.config import settings

class DummyTicker:
    fast_info = type("X", (), {"last_price": 2.5})
    info = {"regularMarketPrice": 2.5}

@pytest.mark.asyncio
async def test_fetch_prices(monkeypatch):
    import yfinance
    monkeypatch.setattr(yfinance, "Ticker", lambda sym: DummyTicker())

    result = await fetch_prices(["SYM"])
    assert "SYM" in result
    assert result["SYM"]["price"] == 2.5

@pytest.mark.asyncio
async def test_poll_loop_once(monkeypatch):
    # Track that fetch_prices gets called
    calls = []

    async def fake_fetch(tickers):
        calls.append(True)
        return {t: {"price": 1, "ts": 0, "raw": {}} for t in tickers}

    # Patch both fetch_prices *and* the publish function in polling's namespace
    monkeypatch.setattr("app.polling.fetch_prices", fake_fetch)
    monkeypatch.setattr("app.polling.publish_price_changes", lambda data: asyncio.sleep(0))

    # Make poll loop run immediately
    settings.POLL_FREQ = 0

    # Run one iteration then cancel
    task = asyncio.create_task(poll_loop())
    asyncio.get_event_loop().call_later(0.1, task.cancel)
    with pytest.raises(asyncio.CancelledError):
        await task

    assert calls, "poll_loop did not call fetch_prices"
