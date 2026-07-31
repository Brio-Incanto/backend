from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    # off by default — local dev works without a Redis instance running;
    # turn on explicitly once one is available.
    USE_REDIS_DRAFT_HISTORY: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
