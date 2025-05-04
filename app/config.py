import logging

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    TICKERS: str = ""
    POLL_FREQ: int = Field(default=5, ge=1)
    REDIS_URL: str = "redis://localhost:6379"

    @property
    def tickers_list(self):
        return [s.strip() for s in self.TICKERS.split(",") if s.strip()]

    model_config = {"env_file": ".env"}


settings = Settings()
logger.info(f"Loaded config: TICKERS={settings.tickers_list}, POLL_FREQ={settings.POLL_FREQ}")
