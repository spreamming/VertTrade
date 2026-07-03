import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'market_watch.db'}"


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "VertTrade")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


@lru_cache
def get_settings() -> Settings:
    return Settings()
