from functools import lru_cache
import os
from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


def app_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ShiCi"
    return BACKEND_DIR.parent / "data"


def env_file_path() -> Path:
    return app_data_dir() / ".env" if getattr(sys, "frozen", False) else BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "拾词 API"
    app_env: str = "development"
    database_path: str = "../data/learn_english.db"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    model_config = SettingsConfigDict(
        env_file=env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_file(self) -> Path:
        if getattr(sys, "frozen", False):
            return app_data_dir() / "learn_english.db"
        path = Path(self.database_path)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def env_file(self) -> Path:
        return env_file_path()


@lru_cache
def get_settings() -> Settings:
    return Settings()
