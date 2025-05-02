import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Settings:
    """
    Simple environment-based configuration.
    """
    def __init__(self):
        # Comma-separated list of ticker symbols
        raw = os.getenv("TICKERS", "")
        self.TICKERS = [s.strip() for s in raw.split(',') if s.strip()]
        # Polling interval in seconds (default 5)
        self.POLL_FREQ = int(os.getenv("POLL_FREQ", "5"))

# Instantiate settings
settings = Settings()