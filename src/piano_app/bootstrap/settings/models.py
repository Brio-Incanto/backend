from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import SecretStr
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
    """One flat env-var namespace (pydantic-settings' default source), grouped
    below by what each field configures — NOT nested into real sub-models: a
    nested ``BaseModel`` only picks up flat top-level env vars (``JWT_SECRET``)
    via a custom settings source, not for free, and this project's ``.env``
    already commits to the flat names (verified before choosing this shape)."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
    )

    # --- Persistence: system data and independently stored draft history.
    # DATABASE_URL is unconditional (canon scores + auth). REDIS_URL is used by
    # REDIS/TIERED; DRAFT_DATABASE_URL is used only by TIERED's cold archive.
    DRAFT_HISTORY_BACKEND: DraftHistoryBackend = DraftHistoryBackend.MEMORY
    DATABASE_URL: str
    DRAFT_DATABASE_URL: str | None = None
    REDIS_URL: str | None = None

    # --- Google Sign-In: the id_token audience(s) this deployment accepts.
    GOOGLE_CLIENT_IDS: tuple[str, ...] = ()

    # --- Access tokens (JWT): issuance and verification.
    JWT_SECRET: SecretStr
    JWT_ISSUER: str = "piano-app"
    JWT_AUDIENCE: str = "piano-api"
    JWT_ACCESS_TTL_SECONDS: int = 30 * 60

    # --- Refresh sessions / cookie.
    AUTH_REFRESH_TTL_SECONDS: int = 30 * 24 * 60 * 60
    AUTH_REFRESH_COOKIE_SECURE: bool = True
    AUTH_REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # --- HTTP: CORS.
    CORS_ORIGINS: tuple[str, ...] = ()
