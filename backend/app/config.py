import json
import os
import sys
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_NAME = "VertTrade"


def _default_app_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def is_packaged_runtime() -> bool:
    return os.getenv("VERTTRADE_PACKAGED") == "1"


@lru_cache
def get_data_dir() -> Path:
    override = os.getenv("VERTTRADE_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if is_packaged_runtime() or os.getenv("APP_ENV") == "production":
        return _default_app_data_dir()
    return PROJECT_ROOT / "data"


def get_database_url() -> str:
    override = os.getenv("DATABASE_URL")
    if override:
        return override
    database_path = get_data_dir() / "market_watch.db"
    return f"sqlite:///{database_path}"


def get_settings_path() -> Path:
    return get_data_dir() / "settings.json"


def load_user_settings() -> dict:
    path = get_settings_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


class Settings(BaseModel):
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", APP_NAME))
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_url: str = Field(default_factory=get_database_url)
    data_dir: str = Field(default_factory=lambda: str(get_data_dir()))
    packaged: bool = Field(default_factory=is_packaged_runtime)
    watchlist_live_refresh_limit: int = 20


@lru_cache
def get_settings() -> Settings:
    user_settings = load_user_settings()
    settings = Settings()
    limit = user_settings.get("watchlist_live_refresh_limit")
    if isinstance(limit, int) and limit > 0:
        settings = settings.model_copy(update={"watchlist_live_refresh_limit": limit})
    return settings


def clear_settings_cache() -> None:
    get_settings.cache_clear()
    get_data_dir.cache_clear()
