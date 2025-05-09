import asyncio

import pytest

from app.config import settings
from app.polling import fetch_prices, poll_loop


class DummyTicker:
    def __init__(self, *args, **kwargs):
        pass

    fast_info = type("X", (), {"last_price": 2.5})
    info = {"regularMarketPrice": 2.5, "quoteType": "equity", "regularMarketTime": 1714680000}


@pytest.mark.asyncio
async def test_fetch_prices(monkeypatch):
    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", DummyTicker)

    result = await fetch_prices(["SYM"])
    assert "SYM" in result
    assert result["SYM"]["price"] == 2.5
    assert "marketTime" in result["SYM"]
    assert "publishedTime" in result["SYM"]
    assert isinstance(result["SYM"]["meta"], dict)


@pytest.mark.asyncio
async def test_poll_loop_once(monkeypatch):
    calls = []

    async def fake_fetch(tickers):
        calls.append("fetched")
        return {
            t: {
                "price": 1,
                "marketTime": "2025-05-03T00:00:00Z",
                "publishedTime": "2025-05-03T00:00:00Z",
                "meta": {},
            }
            for t in tickers
        }

    # Prevent actual Redis/publish
    async def fake_publish(data):
        calls.append("published")
        await asyncio.sleep(0)

    monkeypatch.setattr("app.polling.fetch_prices", fake_fetch)
    monkeypatch.setattr("app.polling.publish_price_changes", fake_publish)

    # Reduce backoff to zero for testing
    monkeypatch.setattr(settings, "POLL_FREQ", 0)

    # Run a single iteration and cancel
    task = asyncio.create_task(poll_loop())
    asyncio.get_event_loop().call_later(0.1, task.cancel)

    with pytest.raises(asyncio.CancelledError):
        await task

    assert "fetched" in calls, "poll_loop did not call fetch_prices"
    assert "published" in calls, "poll_loop did not call publish_price_changes"
