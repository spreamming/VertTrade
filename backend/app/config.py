from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "VertTrade"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/market_watch.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
