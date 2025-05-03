import os
import logging
from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    TICKERS: str = ""
    POLL_FREQ: int = Field(default=5, ge=1)

    @property
    def tickers_list(self):
        return [s.strip() for s in self.TICKERS.split(",") if s.strip()]

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
logger.info(f"Loaded config: TICKERS={settings.tickers_list}, POLL_FREQ={settings.POLL_FREQ}")
