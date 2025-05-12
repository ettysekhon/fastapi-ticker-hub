import pytest
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_snapshot(monkeypatch):
    async def _fake():
        return {"AAPL": {"price": 150.0}}

    import api.main

    monkeypatch.setattr(api.state, "get_prices", _fake)
    monkeypatch.setattr(api.main, "get_prices", _fake)


def test_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_get_all_tickers():
    res = client.get("/tickers")
    assert res.status_code == 200
    assert res.json() == {"AAPL": {"price": 150.0}}


def test_get_one_ticker_found():
    res = client.get("/tickers/AAPL")
    assert res.status_code == 200
    assert res.json() == {"price": 150.0}


def test_get_one_ticker_not_found():
    res = client.get("/tickers/GOOG")
    assert res.status_code == 404
