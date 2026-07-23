"""Application configuration.

Settings are loaded from environment variables (optionally via a ``.env``
file), keeping configuration out of the codebase.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central, immutable application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", frozen=True)

    app_name: str = "chat-api"
    debug: bool = False

    database_url: str = "sqlite:///./chat_data.db"

    # Content filtering: a deliberately simple, configurable word list.
    banned_words: str = "badword,offensive"

    # Pagination guardrails for list endpoints.
    default_page_limit: int = 20
    max_page_limit: int = 100

    # Authentication: API key required on protected endpoints.
    # Empty string disables auth (useful for local development and tests).
    api_key: str = ""

    # Rate limiting: requests allowed per client, per window.
    # Empty string disables the limiter (useful in tests).
    rate_limit: str = ""

    @property
    def banned_words_list(self) -> list[str]:
        """Return the banned words as a normalized list."""
        return [w.strip().lower() for w in self.banned_words.split(",") if w.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
