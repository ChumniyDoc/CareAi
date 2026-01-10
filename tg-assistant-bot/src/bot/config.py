from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    database_url: str
    tz: str = "Asia/Almaty"
    morning_time: str = "09:00"
    evening_time: str = "21:30"
    weekly_review_time: str = "Sunday 18:00"

    def resolve_bot_token(self) -> str:
        secret_path = Path("/run/secrets/bot_token")
        if secret_path.exists():
            return secret_path.read_text().strip()
        return self.bot_token


def load_settings() -> Settings:
    settings = Settings()
    if not settings.resolve_bot_token():
        raise SystemExit("BOT_TOKEN is required")
    return settings
