from enum import StrEnum
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class DraftHistoryBackend(StrEnum):
    """Which adapter backs the ``DraftHistory`` port — one switch instead of the
    old pair of independent booleans (``USE_REDIS_DRAFT_HISTORY`` /
    ``USE_POSTGRES_COLD_STORAGE``), which could express the nonsensical
    "cold storage on, hot tier off" combination.

    MEMORY — single-process, no external services (default; local dev with
             nothing else running).
    REDIS  — hot tier only, no durable spill (needs Redis).
    TIERED — Redis hot + Postgres cold, via TieredDraftHistory (needs both).
    """

    MEMORY = "memory"
    REDIS = "redis"
    TIERED = "tiered"


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    # in-process by default — local dev works without Redis/Postgres running;
    # switch explicitly once the backing service(s) are available.
    DRAFT_HISTORY_BACKEND: DraftHistoryBackend = DraftHistoryBackend.MEMORY
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://piano:piano@localhost:5432/piano"
