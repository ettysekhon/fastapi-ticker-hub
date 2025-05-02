from fastapi.testclient import TestClient
from app.main import app
from app.state import state

client = TestClient(app)

def test_get_all_empty():
    state.prices = {}
    r = client.get("/tickers")
    assert r.status_code == 200
    assert r.json() == {}

def test_get_one_not_found():
    state.prices = {}
    r = client.get("/tickers/NOTHING")
    assert r.status_code == 404

def test_get_one_success():
    state.prices = {"FOO": {"price": 9, "ts": 0, "raw": {}}}
    r = client.get("/tickers/FOO")
    assert r.status_code == 200
    assert r.json()["price"] == 9
