from pathlib import Path

from backend.app.config import clear_settings_cache, get_data_dir, get_settings


def test_data_dir_uses_env_override(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VERTTRADE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("VERTTRADE_PACKAGED", raising=False)
    clear_settings_cache()

    assert get_data_dir() == tmp_path
    settings = get_settings()
    assert settings.database_url == f"sqlite:///{tmp_path / 'market_watch.db'}"
    assert settings.data_dir == str(tmp_path)


def test_packaged_runtime_uses_app_data_dir(monkeypatch):
    monkeypatch.delenv("VERTTRADE_DATA_DIR", raising=False)
    monkeypatch.setenv("VERTTRADE_PACKAGED", "1")
    clear_settings_cache()

    settings = get_settings()
    assert settings.packaged is True
    assert "VertTrade" in settings.data_dir


def test_user_settings_override_refresh_limit(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VERTTRADE_DATA_DIR", str(tmp_path))
    clear_settings_cache()
    (tmp_path / "settings.json").write_text(
        '{"watchlist_live_refresh_limit": 12}',
        encoding="utf-8",
    )
    clear_settings_cache()

    settings = get_settings()
    assert settings.watchlist_live_refresh_limit == 12
