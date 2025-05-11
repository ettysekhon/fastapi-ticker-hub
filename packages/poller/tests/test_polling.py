import pytest
from poller.main import slim_info
from poller.settings import tickers_list
from poller.state import _snapshot, update_prices


# --- tickers_list tests ---
def test_tickers_list_empty(monkeypatch):
    monkeypatch.setenv("TICKERS", "")
    assert tickers_list() == []


def test_tickers_list_parsing(monkeypatch):
    monkeypatch.setenv("TICKERS", " AAPL , GOOG,,MSFT ")
    assert tickers_list() == ["AAPL", "GOOG", "MSFT"]


# --- slim_info tests ---
COMMON_INFO = {
    "symbol": "AAPL",
    "shortName": "Apple Inc.",
    "currency": "USD",
    "regularMarketPrice": 150.0,
    "regularMarketChange": 1.5,
    "regularMarketChangePercent": 1.0,
    "marketState": "CLOSED",
}


def test_slim_info_common_fields():
    meta = slim_info(COMMON_INFO)
    assert meta["symbol"] == "AAPL"
    assert meta["name"] == "Apple Inc."
    assert meta["currency"] == "USD"
    assert meta["price"] == 150.0
    assert meta["change"] == 1.5
    assert meta["changePercent"] == 1.0
    assert meta["marketState"] == "CLOSED"
    # FUTURES_EXTRA keys should not be present
    assert "expiry" not in meta


def test_slim_info_future_fields():
    info = COMMON_INFO.copy()
    info.update(
        {
            "quoteType": "FUTURE",
            "expireIsoDate": "2025-06-30",
            "underlyingSymbol": "CL",
            "openInterest": 1234,
        }
    )
    meta = slim_info(info)
    assert meta["expiry"] == "2025-06-30"
    assert meta["underlying"] == "CL"
    assert meta["openInterest"] == 1234


# --- update_prices tests ---
@pytest.mark.asyncio
async def test_update_prices_merges_snapshot(tmp_path, monkeypatch):
    # Clear in-memory snapshot
    _snapshot.clear()

    # First update
    data1 = {"AAPL": {"price": 100}}
    await update_prices(data1)
    assert _snapshot == data1

    # Second update with new symbol and changed price
    data2 = {"GOOG": {"price": 200}, "AAPL": {"price": 101}}
    await update_prices(data2)
    assert _snapshot["GOOG"]["price"] == 200
    assert _snapshot["AAPL"]["price"] == 101
