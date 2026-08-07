from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from piano_app.adapters.inbound.http import (
    build_draft_router,
    build_edit_router,
    build_save_router,
    register_exception_handlers,
)
from piano_app.adapters.outbound.in_memory.draft_history import InMemoryDraftHistory
from piano_app.adapters.outbound.postgres.draft_archive import PostgresDraftArchive
from piano_app.adapters.outbound.postgres.engine import create_engine as create_pg_engine
from piano_app.adapters.outbound.postgres.engine import create_session_factory
from piano_app.adapters.outbound.postgres.score_uow import PostgresScoreUoWFactory
from piano_app.adapters.outbound.redis.client import create_client as create_redis_client
from piano_app.adapters.outbound.redis.draft_cache import RedisDraftCache
from piano_app.adapters.outbound.redis.draft_history import RedisDraftHistory
from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.adapters.outbound.tiered_draft_history import TieredDraftHistory
from piano_app.application.ports import DraftHistory, ScoreUoWFactory
from piano_app.application.use_cases.score import SaveScoreService, ScoreEditService
from piano_app.application.use_cases.score.draft.service import DraftService
from piano_app.domain.score.document.services.mutation.compiler import MutationCompiler
from piano_app.domain.score.document.services.mutation.engine import MutationEngine
from piano_app.domain.score.document.services.mutation.engine.analyzers.material import (
    CreateNoteAnalyzer,
    CreateNoteCarrierAnalyzer,
    CreateRestAnalyzer,
    CreateRestCarrierAnalyzer,
    DeleteNoteAnalyzer,
    DeleteNoteCarrierAnalyzer,
    DeleteRestAnalyzer,
    DeleteRestCarrierAnalyzer,
)
from piano_app.domain.score.document.services.mutation.engine.analyzers.relations import (
    CreateTieAnalyzer,
    DeleteRelationAnalyzer,
)
from piano_app.domain.score.document.services.mutation.engine.analyzers.rhythmic import (
    CreateLeafAnalyzer,
    DeleteLeafAnalyzer,
    DeleteRhythmicGroupAnalyzer,
)
from piano_app.domain.score.document.services.mutation.engine.analyzers.temporal import (
    CreateTemporalAnchorAnalyzer,
    DeleteTemporalAnchorAnalyzer,
)
from piano_app.domain.score.document.services.mutation.engine.handlers.material import (
    CreateNoteCarrierHandler,
    CreateNoteHandler,
    CreateRestCarrierHandler,
    CreateRestHandler,
    DeleteNoteCarrierHandler,
    DeleteNoteHandler,
    DeleteRestCarrierHandler,
    DeleteRestHandler,
)
from piano_app.domain.score.document.services.mutation.engine.handlers.relations import (
    CreateTieHandler,
    DeleteRelationHandler,
)
from piano_app.domain.score.document.services.mutation.engine.handlers.rhythmic import (
    CreateLeafHandler,
    DeleteLeafHandler,
    DeleteRhythmicGroupHandler,
)
from piano_app.domain.score.document.services.mutation.engine.handlers.temporal import (
    CreateTemporalAnchorHandler,
    DeleteTemporalAnchorHandler,
)
from piano_app.domain.score.document.services.mutation.engine.postprocessors import (
    CleanupPostprocessor,
    FillGapsPostprocessor,
    MutatedStatePostprocessor,
)
from piano_app.domain.score.document.services.mutation.engine.registry import (
    MutationAnalyzerRegistry,
    MutationHandlerRegistry,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateNoteAction,
    CreateNoteCarrierAction,
    CreateRestAction,
    CreateRestCarrierAction,
    DeleteNoteAction,
    DeleteNoteCarrierAction,
    DeleteRestAction,
    DeleteRestCarrierAction,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.relations import (
    CreateTieAction,
    DeleteRelationAction,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.rhythmic import (
    CreateLeafAction,
    DeleteLeafAction,
    DeleteRhythmicGroupAction,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.temporal import (
    CreateTemporalAnchorAction,
    DeleteTemporalAnchorAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.material import (
    CreateNoteCarrierRequest,
    CreateNoteRequest,
    CreateRestCarrierRequest,
    CreateRestRequest,
    DeleteNoteCarrierRequest,
    DeleteNoteRequest,
    DeleteRestCarrierRequest,
    DeleteRestRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.relations import (
    CreateTieRequest,
    DeleteRelationRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    CreateLeafRequest,
    DeleteLeafRequest,
    DeleteRhythmicGroupRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
    DeleteTemporalAnchorRequest,
)

from .settings import DraftHistoryBackend, Settings, load_settings


def build_analyzer_registry() -> MutationAnalyzerRegistry:
    registry: MutationAnalyzerRegistry = MutationAnalyzerRegistry()

    # material
    registry.register(request_type=CreateNoteRequest, analyzer=CreateNoteAnalyzer())
    registry.register(request_type=DeleteNoteRequest, analyzer=DeleteNoteAnalyzer())

    registry.register(request_type=CreateRestRequest, analyzer=CreateRestAnalyzer())
    registry.register(request_type=DeleteRestRequest, analyzer=DeleteRestAnalyzer())

    registry.register(request_type=CreateNoteCarrierRequest, analyzer=CreateNoteCarrierAnalyzer())
    registry.register(request_type=DeleteNoteCarrierRequest, analyzer=DeleteNoteCarrierAnalyzer())

    registry.register(request_type=CreateRestCarrierRequest, analyzer=CreateRestCarrierAnalyzer())
    registry.register(request_type=DeleteRestCarrierRequest, analyzer=DeleteRestCarrierAnalyzer())

    # relations
    registry.register(request_type=CreateTieRequest, analyzer=CreateTieAnalyzer())

    registry.register(request_type=DeleteRelationRequest, analyzer=DeleteRelationAnalyzer())

    # rhythmic
    registry.register(request_type=CreateLeafRequest, analyzer=CreateLeafAnalyzer())
    registry.register(request_type=DeleteLeafRequest, analyzer=DeleteLeafAnalyzer())

    registry.register(
        request_type=DeleteRhythmicGroupRequest, analyzer=DeleteRhythmicGroupAnalyzer()
    )

    # temporal
    registry.register(
        request_type=CreateTemporalAnchorRequest, analyzer=CreateTemporalAnchorAnalyzer()
    )
    registry.register(
        request_type=DeleteTemporalAnchorRequest, analyzer=DeleteTemporalAnchorAnalyzer()
    )

    return registry


def build_handler_registry() -> MutationHandlerRegistry:
    registry: MutationHandlerRegistry = MutationHandlerRegistry()

    # material
    registry.register(action_type=CreateNoteAction, handler=CreateNoteHandler())
    registry.register(action_type=DeleteNoteAction, handler=DeleteNoteHandler())

    registry.register(action_type=CreateRestAction, handler=CreateRestHandler())
    registry.register(action_type=DeleteRestAction, handler=DeleteRestHandler())

    registry.register(action_type=CreateNoteCarrierAction, handler=CreateNoteCarrierHandler())
    registry.register(action_type=DeleteNoteCarrierAction, handler=DeleteNoteCarrierHandler())

    registry.register(action_type=CreateRestCarrierAction, handler=CreateRestCarrierHandler())
    registry.register(action_type=DeleteRestCarrierAction, handler=DeleteRestCarrierHandler())

    # relations
    registry.register(action_type=CreateTieAction, handler=CreateTieHandler())

    registry.register(action_type=DeleteRelationAction, handler=DeleteRelationHandler())

    # rhythmic
    registry.register(action_type=CreateLeafAction, handler=CreateLeafHandler())
    registry.register(action_type=DeleteLeafAction, handler=DeleteLeafHandler())

    registry.register(action_type=DeleteRhythmicGroupAction, handler=DeleteRhythmicGroupHandler())

    # temporal
    registry.register(action_type=CreateTemporalAnchorAction, handler=CreateTemporalAnchorHandler())
    registry.register(action_type=DeleteTemporalAnchorAction, handler=DeleteTemporalAnchorHandler())

    return registry


def build_postprocessors() -> list[MutatedStatePostprocessor]:
    registry: list[MutatedStatePostprocessor] = []

    registry.append(FillGapsPostprocessor())
    registry.append(CleanupPostprocessor())

    return registry


def build_engine() -> MutationEngine:
    return MutationEngine(
        handler_registry=build_handler_registry(),
        analyzer_registry=build_analyzer_registry(),
        postprocessors=build_postprocessors(),
    )


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
            client: Redis = create_redis_client(database_url=settings.REDIS_URL)
            history: RedisDraftHistory = RedisDraftHistory(client=client, codec=codec)
            stack.push_async_callback(history.aclose)
            return history
        case DraftHistoryBackend.TIERED:
            assert session_factory is not None, (
                "TIERED draft history needs a Postgres session_factory."
            )
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
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app=app)
    app.include_router(build_draft_router(service=draft_service))
    app.include_router(build_edit_router(service=edit_service))
    app.include_router(build_save_router(service=save_service))
    return app
