from app.config import Settings


def test_settings_parsing(monkeypatch):
    monkeypatch.setenv("TICKERS", "A,B,C")
    monkeypatch.setenv("POLL_FREQ", "10")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

    settings = Settings()
    assert settings.tickers_list == ["A", "B", "C"]
    assert settings.POLL_FREQ == 10
    assert settings.REDIS_URL == "redis://localhost:6379"
