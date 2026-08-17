from dataclasses import dataclass

from piano_app.application.errors import EditDraftNotFoundError, MissingScoreError
from piano_app.application.ports import ScoreUoWFactory
from piano_app.application.ports.score.draft_store import (
    DraftNotFoundError,
    DraftStore,
    VersionedDraftDocument,
)
from piano_app.application.use_cases.score.shared import ScoreView
from piano_app.domain.score import Score
from piano_app.domain.score.document import ScoreDocument
from piano_app.domain.score.document.models.structural import Measure, Staff, Voice


@dataclass(frozen=True, slots=True, kw_only=True)
class CreatedDraft:
    draft_id: str
    view: ScoreView


class DraftService:
    def __init__(self, *, storage: DraftStore, score_uow_factory: ScoreUoWFactory) -> None:
        self._storage: DraftStore = storage
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def get_document(self, *, draft_id: str, author_id: str) -> ScoreView:
        try:
            versioned: VersionedDraftDocument = await self._storage.load(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

        return ScoreView(document=versioned.document)

    async def create_draft_from_scratch(self, *, author_id: str) -> CreatedDraft:
        document: ScoreDocument = self._seed_fresh_draft()

        versioned: VersionedDraftDocument = await self._storage.create(
            author_id=author_id,
            ref_score_id=None,
            document=document,
        )
        return CreatedDraft(
            draft_id=versioned.draft_id, view=ScoreView(document=versioned.document)
        )

    async def create_draft_from_score(self, *, score_id: str, author_id: str) -> CreatedDraft:
        async with self._score_uow_factory() as uow:
            # read-only, the uow's rollback-on-exit is a no-op, no explicit commit needed
            base_score: Score | None = await uow.score_repository.get(
                score_id=score_id, viewer_id=author_id
            )

            if base_score is None:
                raise MissingScoreError(score_id=score_id)

        versioned: VersionedDraftDocument = await self._storage.create(
            author_id=author_id,
            ref_score_id=score_id,
            document=base_score.document,
        )
        return CreatedDraft(
            draft_id=versioned.draft_id, view=ScoreView(document=versioned.document)
        )

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
