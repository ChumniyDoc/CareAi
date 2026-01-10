from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    database_url: str
    tz: str = "Europe/Moscow"
    weekly_review_time: str = "Sunday 18:00"
    environment: str = "dev"
    admin_user: str = "admin"
    admin_password: str | None = None
    llm_enabled: bool = False
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_timeout_seconds: int = 120
    llm_temperature: float = 0.2
    llm_max_output_tokens: int = 600
    llm_context_days: int = 30
    llm_summary_target_tokens: int = 1200
    llm_approval_required: bool = True

    def resolve_bot_token(self) -> str:
        secret_path = Path("/run/secrets/bot_token")
        if secret_path.exists():
            return secret_path.read_text().strip()
        return self.bot_token


def load_settings() -> Settings:
    settings = Settings()
    if not settings.resolve_bot_token():
        raise SystemExit("BOT_TOKEN is required")
    if settings.environment != "dev" and not settings.admin_password:
        raise SystemExit("ADMIN_PASSWORD is required for non-dev environments")
    if settings.llm_enabled and settings.llm_provider != "ollama":
        raise SystemExit("Only ollama LLM provider is supported")
    if settings.llm_enabled and not settings.llm_approval_required:
        raise SystemExit("LLM_APPROVAL_REQUIRED must remain true")
    return settings
