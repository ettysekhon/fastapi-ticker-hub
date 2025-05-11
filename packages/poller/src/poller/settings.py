import os

from dotenv import load_dotenv

load_dotenv()


def tickers_list() -> list[str]:
    """
    Read the TICKERS env var _each time_ this is called
    so pytest’s monkeypatch.setenv(...) works.
    """
    raw = os.getenv("TICKERS", "")
    return [s.strip() for s in raw.split(",") if s.strip()]


POLL_FREQ = int(os.getenv("POLL_FREQ", "5"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
