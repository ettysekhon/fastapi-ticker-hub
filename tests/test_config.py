from app.config import Settings

def test_settings_parsing(monkeypatch):
    monkeypatch.setenv("TICKERS", "A,B,C")
    monkeypatch.setenv("POLL_FREQ", "10")

    s = Settings()
    assert s.tickers_list == ["A", "B", "C"]
    assert s.POLL_FREQ == 10