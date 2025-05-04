import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app  # Delayed import

    return TestClient(app)


def test_get_all_empty(client):
    response = client.get("/tickers")
    assert response.status_code == 200
    assert response.json() == {}


def test_get_one_not_found(client):
    response = client.get("/tickers/NOSYMBOL")
    assert response.status_code == 404


def test_get_one_success(client, fake_state):
    fake_state["FOO"] = {"price": 9, "ts": 0, "meta": {}}
    response = client.get("/tickers/FOO")
    assert response.status_code == 200
    assert response.json()["price"] == 9
