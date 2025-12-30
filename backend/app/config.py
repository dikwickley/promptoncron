from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Storage
    database_url: str = "sqlite:////app/data/promptoncron.db"

    # LLM
    llm_provider: str = "mock"  # mock | openai | gemini | deepseek
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    default_llm_model: str = "gpt-4o-mini"

    # Web search
    tavily_api_key: str | None = None

    # Loops
    scheduler_interval: int = 10
    worker_poll_interval: int = 2


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


