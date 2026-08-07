from piano_app.application.contracts.score import CreateScoreCommand
from piano_app.application.errors import EditDraftNotFoundError, MissingScoreError
from piano_app.application.ports import DraftStore, ScoreUoWFactory
from piano_app.application.ports.draft_store import DraftNotFoundError, VersionedDraftDocument
from piano_app.application.ports.score_repository import ScoreNotFoundError
from piano_app.domain.score import Score


class SaveScoreService:
    def __init__(self, *, storage: DraftStore, score_uow_factory: ScoreUoWFactory) -> None:
        self._storage: DraftStore = storage
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def promote(self, *, draft_id: str, author_id: str) -> str:
        try:
            versioned: VersionedDraftDocument = await self._storage.load(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

        if versioned.ref_score_id is None:
            raise MissingScoreError()

        async with self._score_uow_factory() as uow:
            try:
                await uow.score_repository.update(
                    score_id=versioned.ref_score_id,
                    document=versioned.document,
                )
            except ScoreNotFoundError as error:
                raise MissingScoreError(score_id=error.score_id) from error
            await uow.commit()

        return versioned.ref_score_id

    async def create_branch(
        self,
        *,
        draft_id: str,
        author_id: str,
        command: CreateScoreCommand,
    ) -> str:
        try:
            versioned: VersionedDraftDocument = await self._storage.load(draft_id=draft_id)
        except DraftNotFoundError as error:
            raise EditDraftNotFoundError(draft_id=error.draft_id) from error

        async with self._score_uow_factory() as uow:
            if versioned.ref_score_id is not None and not await uow.score_repository.exists(
                score_id=versioned.ref_score_id
            ):
                raise MissingScoreError(score_id=versioned.ref_score_id)

            created: Score = await uow.score_repository.create(
                title=command.title,
                author_id=author_id,
                composer=command.composer,
                derived_from_id=versioned.ref_score_id,
                document=versioned.document,
                is_public=command.is_public,
            )
            await uow.commit()

        return created.id
