from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from piano_app.adapters.inbound.http import (
    CurrentUser,
    CurrentUserOptional,
    build_draft_router,
    build_edit_router,
    build_save_router,
    build_scores_router,
    build_session_router,
    register_exception_handlers,
)
from piano_app.adapters.outbound.auth import JWTAccessTokenService
from piano_app.adapters.outbound.google import GoogleIdentityVerifier
from piano_app.adapters.outbound.in_memory.draft_history import InMemoryDraftHistory
from piano_app.adapters.outbound.postgres.auth.uow import PostgresAuthUoWFactory
from piano_app.adapters.outbound.postgres.engine import create_engine as create_pg_engine
from piano_app.adapters.outbound.postgres.engine import create_session_factory
from piano_app.adapters.outbound.postgres.score.draft_archive import PostgresDraftArchive
from piano_app.adapters.outbound.postgres.score.uow import PostgresScoreUoWFactory
from piano_app.adapters.outbound.redis.client import create_client as create_redis_client
from piano_app.adapters.outbound.redis.draft_cache import RedisDraftCache
from piano_app.adapters.outbound.redis.draft_history import RedisDraftHistory
from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.adapters.outbound.tiered_draft_history import TieredDraftHistory
from piano_app.application.ports import DraftHistory, ScoreUoWFactory
from piano_app.application.use_cases.auth import AuthService
from piano_app.application.use_cases.score import (
    SaveScoreService,
    ScoreCatalogService,
    ScoreEditService,
)
from piano_app.application.use_cases.score.draft.service import DraftService
from piano_app.domain.score.document.services.mutation import (
    MutationCompiler,
    MutationEngine,
    build_engine,
)

from .settings import DraftHistoryBackend, Settings, load_settings


def build_draft_history(
    *,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession] | None,
    codec: ScoreDocumentCodec,
    stack: AsyncExitStack,
) -> DraftHistory:
    """Constructs the configured draft-history adapter, per ``settings.DRAFT_HISTORY_BACKEND``
    (in-memory by default), and registers ITS OWN cleanup on ``stack`` right here — the
    caller (``build_app``) never inspects the returned adapter's type or reaches for a
    connection it doesn't know about; each backend owns both its construction and its
    teardown as one unit. ``session_factory`` is only used by TIERED (its Postgres cold
    tier); MEMORY/REDIS ignore it. MEMORY registers nothing (no connection to close)."""
    match settings.DRAFT_HISTORY_BACKEND:
        case DraftHistoryBackend.MEMORY:
            return InMemoryDraftHistory()
        case DraftHistoryBackend.REDIS:
            assert settings.REDIS_URL is not None, "REDIS draft history needs REDIS_URL set."
            client: Redis = create_redis_client(database_url=settings.REDIS_URL)
            history: RedisDraftHistory = RedisDraftHistory(client=client, codec=codec)
            stack.push_async_callback(history.aclose)
            return history
        case DraftHistoryBackend.TIERED:
            assert session_factory is not None, (
                "TIERED draft history needs a Postgres session_factory."
            )
            assert settings.REDIS_URL is not None, "TIERED draft history needs REDIS_URL set."
            cache: RedisDraftCache = RedisDraftCache(
                client=create_redis_client(database_url=settings.REDIS_URL), codec=codec
            )
            archive: PostgresDraftArchive = PostgresDraftArchive(
                session_factory=session_factory, codec=codec
            )
            tiered: TieredDraftHistory = TieredDraftHistory(archive=archive, cache=cache)
            stack.push_async_callback(tiered.aclose)
            return tiered


def build_pg_engine(*, settings: Settings, stack: AsyncExitStack) -> AsyncEngine:
    """The one Postgres engine for the whole app. Every Postgres-touching adapter
    (``ScoreRepository``; ``PostgresDraftArchive`` when ``DRAFT_HISTORY_BACKEND=tiered``)
    reuses this single connection pool instead of each opening its own — they're all
    just adapters over the same database. Pure construction only — no connection is
    opened until first use. Registers its own disposal on ``stack``, same as every
    other resource-owning builder."""
    engine: AsyncEngine = create_pg_engine(database_url=settings.DATABASE_URL)
    stack.push_async_callback(engine.dispose)
    return engine


def build_score_uow_factory(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    codec: ScoreDocumentCodec,
) -> ScoreUoWFactory:
    """Constructs the canon-storage (score) unit-of-work factory. Always Postgres — a
    score repository has no non-Postgres fallback, unlike draft history."""
    return PostgresScoreUoWFactory(session_factory=session_factory, codec=codec)


def build_app(*, settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings or load_settings()
    codec: ScoreDocumentCodec = ScoreDocumentCodec()

    # every resource-owning builder below registers its own cleanup on this stack, at
    # the point where it's constructed — build_app never inspects what it got back to
    # decide whether/how to close it (see build_pg_engine / build_draft_history).
    stack: AsyncExitStack = AsyncExitStack()

    pg_engine: AsyncEngine = build_pg_engine(settings=resolved_settings, stack=stack)
    session_factory: async_sessionmaker[AsyncSession] = create_session_factory(engine=pg_engine)

    access_tokens: JWTAccessTokenService = JWTAccessTokenService(
        secret=resolved_settings.JWT_SECRET.get_secret_value(),
        issuer=resolved_settings.JWT_ISSUER,
        audience=resolved_settings.JWT_AUDIENCE,
        ttl=timedelta(seconds=resolved_settings.JWT_ACCESS_TTL_SECONDS),
    )
    auth_service: AuthService = AuthService(
        identity_verifier=GoogleIdentityVerifier(
            allowed_audiences=frozenset(resolved_settings.GOOGLE_CLIENT_IDS)
        ),
        auth_uow_factory=PostgresAuthUoWFactory(
            session_factory=session_factory,
            refresh_token_ttl=timedelta(seconds=resolved_settings.AUTH_REFRESH_TTL_SECONDS),
        ),
        access_tokens=access_tokens,
    )
    current_user: CurrentUser = CurrentUser(access_tokens=access_tokens)
    current_user_optional: CurrentUserOptional = CurrentUserOptional(access_tokens=access_tokens)

    engine: MutationEngine = build_engine()
    compiler: MutationCompiler = MutationCompiler()
    history: DraftHistory = build_draft_history(
        settings=resolved_settings, session_factory=session_factory, codec=codec, stack=stack
    )
    edit_service: ScoreEditService = ScoreEditService(
        engine=engine, compiler=compiler, history=history
    )

    score_uow_factory: ScoreUoWFactory = build_score_uow_factory(
        session_factory=session_factory, codec=codec
    )
    draft_service: DraftService = DraftService(storage=history, score_uow_factory=score_uow_factory)
    save_service: SaveScoreService = SaveScoreService(
        storage=history, score_uow_factory=score_uow_factory
    )
    catalog_service: ScoreCatalogService = ScoreCatalogService(score_uow_factory=score_uow_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # runs on the real (uvicorn/ASGI-server) event loop, unlike a bare asyncio.run()
        # at import time, which would bind connections to a loop that's closed by the
        # time requests actually arrive.
        try:
            yield
        finally:
            await stack.aclose()

    app: FastAPI = FastAPI(title="Piano App", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app=app)
    app.include_router(
        build_session_router(
            service=auth_service,
            current_user=current_user,
            refresh_cookie_secure=resolved_settings.AUTH_REFRESH_COOKIE_SECURE,
            refresh_cookie_samesite=resolved_settings.AUTH_REFRESH_COOKIE_SAMESITE,
            refresh_cookie_max_age=resolved_settings.AUTH_REFRESH_TTL_SECONDS,
        )
    )
    app.include_router(
        build_scores_router(
            service=catalog_service,
            current_user=current_user,
            current_user_optional=current_user_optional,
        )
    )
    app.include_router(build_draft_router(service=draft_service, current_user=current_user))
    app.include_router(build_edit_router(service=edit_service, current_user=current_user))
    app.include_router(build_save_router(service=save_service, current_user=current_user))
    return app
