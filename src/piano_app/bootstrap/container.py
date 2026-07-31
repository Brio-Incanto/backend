from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from piano_app.adapters.inbound.http import (
    build_edit_router,
    register_exception_handlers,
)
from piano_app.adapters.outbound.codec import ScoreDocumentCodec
from piano_app.adapters.outbound.in_memory_draft_history import InMemoryDraftHistory
from piano_app.adapters.outbound.redis_draft_history import RedisDraftHistory
from piano_app.application.ports import DraftHistory
from piano_app.application.use_cases.score import ScoreEditService
from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.services.mutation.compiler import MutationCompiler
from piano_app.domain.score.services.mutation.engine import MutationEngine
from piano_app.domain.score.services.mutation.engine.analyzers.material import (
    CreateNoteAnalyzer,
    CreateNoteCarrierAnalyzer,
    CreateRestAnalyzer,
    CreateRestCarrierAnalyzer,
    DeleteNoteAnalyzer,
    DeleteNoteCarrierAnalyzer,
    DeleteRestAnalyzer,
    DeleteRestCarrierAnalyzer,
)
from piano_app.domain.score.services.mutation.engine.analyzers.relations import (
    CreateTieAnalyzer,
    DeleteRelationAnalyzer,
)
from piano_app.domain.score.services.mutation.engine.analyzers.rhythmic import (
    CreateLeafAnalyzer,
    DeleteLeafAnalyzer,
    DeleteRhythmicGroupAnalyzer,
)
from piano_app.domain.score.services.mutation.engine.analyzers.temporal import (
    CreateTemporalAnchorAnalyzer,
    DeleteTemporalAnchorAnalyzer,
)
from piano_app.domain.score.services.mutation.engine.handlers.material import (
    CreateNoteCarrierHandler,
    CreateNoteHandler,
    CreateRestCarrierHandler,
    CreateRestHandler,
    DeleteNoteCarrierHandler,
    DeleteNoteHandler,
    DeleteRestCarrierHandler,
    DeleteRestHandler,
)
from piano_app.domain.score.services.mutation.engine.handlers.relations import (
    CreateTieHandler,
    DeleteRelationHandler,
)
from piano_app.domain.score.services.mutation.engine.handlers.rhythmic import (
    CreateLeafHandler,
    DeleteLeafHandler,
    DeleteRhythmicGroupHandler,
)
from piano_app.domain.score.services.mutation.engine.handlers.temporal import (
    CreateTemporalAnchorHandler,
    DeleteTemporalAnchorHandler,
)
from piano_app.domain.score.services.mutation.engine.postprocessors import (
    CleanupPostprocessor,
    FillGapsPostprocessor,
    MutatedStatePostprocessor,
)
from piano_app.domain.score.services.mutation.engine.registry import (
    MutationAnalyzerRegistry,
    MutationHandlerRegistry,
)
from piano_app.domain.score.services.mutation.instructions.actions.material import (
    CreateNoteAction,
    CreateNoteCarrierAction,
    CreateRestAction,
    CreateRestCarrierAction,
    DeleteNoteAction,
    DeleteNoteCarrierAction,
    DeleteRestAction,
    DeleteRestCarrierAction,
)
from piano_app.domain.score.services.mutation.instructions.actions.relations import (
    CreateTieAction,
    DeleteRelationAction,
)
from piano_app.domain.score.services.mutation.instructions.actions.rhythmic import (
    CreateLeafAction,
    DeleteLeafAction,
    DeleteRhythmicGroupAction,
)
from piano_app.domain.score.services.mutation.instructions.actions.temporal import (
    CreateTemporalAnchorAction,
    DeleteTemporalAnchorAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.material import (
    CreateNoteCarrierRequest,
    CreateNoteRequest,
    CreateRestCarrierRequest,
    CreateRestRequest,
    DeleteNoteCarrierRequest,
    DeleteNoteRequest,
    DeleteRestCarrierRequest,
    DeleteRestRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations import (
    DeleteRelationRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations.tie import (
    CreateTieRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.rhythmic import (
    CreateLeafRequest,
    DeleteLeafRequest,
    DeleteRhythmicGroupRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.temporal import (
    CreateTemporalAnchorRequest,
    DeleteTemporalAnchorRequest,
)

from .seed import build_seed_document
from .settings import Settings, load_settings


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


_DEFAULT_SCORE_ID: str = "default"


def build_engine() -> MutationEngine:
    return MutationEngine(
        handler_registry=build_handler_registry(),
        analyzer_registry=build_analyzer_registry(),
        postprocessors=build_postprocessors(),
    )


def build_draft_history(
    *,
    settings: Settings,
    seed: ScoreDocument,
) -> DraftHistory:
    """Constructs the configured draft-history adapter (in-memory by default; Redis when
    ``USE_REDIS_DRAFT_HISTORY`` is set). Pure construction only — no I/O: the in-memory
    adapter is seeded synchronously here (no I/O to do), but Redis seeding needs a real
    event loop and happens later, in the app's lifespan (see ``build_app``)."""
    if not settings.USE_REDIS_DRAFT_HISTORY:
        return InMemoryDraftHistory(drafts={_DEFAULT_SCORE_ID: seed})

    client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return RedisDraftHistory(client=client, codec=ScoreDocumentCodec())


def build_app(*, settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings or load_settings()
    engine: MutationEngine = build_engine()
    compiler: MutationCompiler = MutationCompiler()
    seed: ScoreDocument = build_seed_document(engine=engine, compiler=compiler)
    history: DraftHistory = build_draft_history(settings=resolved_settings, seed=seed)
    service: ScoreEditService = ScoreEditService(engine=engine, compiler=compiler, history=history)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # runs on the real (uvicorn/ASGI-server) event loop, unlike a bare asyncio.run()
        # at import time, which would bind connections to a loop that's closed by the
        # time requests actually arrive.
        if isinstance(history, RedisDraftHistory):
            await history.ensure_seeded(draft_id=_DEFAULT_SCORE_ID, document=seed)
        try:
            yield
        finally:
            if isinstance(history, RedisDraftHistory):
                await history.aclose()

    app: FastAPI = FastAPI(title="Piano App", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app=app)
    app.include_router(build_edit_router(service=service))
    return app
