from collections.abc import Sequence
from dataclasses import dataclass

from piano_app.application.ports import ScoreUoWFactory
from piano_app.application.ports.score import (
    DraftMeta,
    DraftStore,
    VersionedDraftDocument,
)
from piano_app.application.use_cases.score.shared import (
    ScoreView,
    require_accessible_draft,
    require_readable_score,
)
from piano_app.domain.score import Score
from piano_app.domain.score.document import ScoreDocument
from piano_app.domain.score.document.models.structural import Measure, Staff, Voice

_UNTITLED_DRAFT: str = "Untitled"


@dataclass(frozen=True, slots=True, kw_only=True)
class CreatedDraft:
    draft_id: str
    view: ScoreView


class DraftService:
    def __init__(self, *, storage: DraftStore, score_uow_factory: ScoreUoWFactory) -> None:
        self._storage: DraftStore = storage
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def get_document(self, *, draft_id: str, viewer_id: str) -> ScoreView:
        versioned: VersionedDraftDocument = await require_accessible_draft(
            storage=self._storage,
            draft_id=draft_id,
            viewer_id=viewer_id,
        )

        return ScoreView(document=versioned.document)

    async def create_draft_from_scratch(self, *, actor_id: str) -> CreatedDraft:
        document: ScoreDocument = self._seed_fresh_draft()

        versioned: VersionedDraftDocument = await self._storage.create(
            title=_UNTITLED_DRAFT,
            author_id=actor_id,
            ref_score_id=None,
            document=document,
        )
        return CreatedDraft(
            draft_id=versioned.draft_id, view=ScoreView(document=versioned.document)
        )

    async def create_draft_from_score(self, *, score_id: str, actor_id: str) -> CreatedDraft:
        async with self._score_uow_factory() as uow:
            # read-only, the uow's rollback-on-exit is a no-op, no explicit commit needed
            base_score: Score = await require_readable_score(
                score_repository=uow.score_repository,
                score_id=score_id,
                viewer_id=actor_id,
            )

        versioned: VersionedDraftDocument = await self._storage.create(
            title=base_score.meta.title,
            author_id=actor_id,
            ref_score_id=score_id,
            document=base_score.document,
        )
        return CreatedDraft(
            draft_id=versioned.draft_id, view=ScoreView(document=versioned.document)
        )

    async def list_author_drafts(self, *, author_id: str) -> Sequence[DraftMeta]:
        return await self._storage.list_by_author(author_id=author_id)

    # TODO clean up by delegating creation of voices, staffs, measures
    #  to the aggregate root (ScoreDocument)
    def _seed_fresh_draft(self) -> ScoreDocument:
        def _voices() -> list[Voice]:
            return [Voice() for _ in range(3)]

        def _staffs() -> list[Staff]:
            return [Staff() for _ in range(2)]

        def _measures() -> list[Measure]:
            return [Measure.create() for _ in range(20)]

        document: ScoreDocument = ScoreDocument.create(
            voices=_voices(), staffs=_staffs(), measures=_measures()
        )
        return document
