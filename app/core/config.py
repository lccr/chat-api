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

    @property
    def banned_words_list(self) -> list[str]:
        """Return the banned words as a normalized list."""
        return [w.strip().lower() for w in self.banned_words.split(",") if w.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()


