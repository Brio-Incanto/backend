from piano_app.application.contracts.score import CreateScoreCommand
from piano_app.application.errors import EditDraftNotFoundError, MissingScoreError
from piano_app.application.errors import ScoreNotOwnedError as AppScoreNotOwnedError
from piano_app.application.errors import ScoreVersionClashError as AppScoreVersionClashError
from piano_app.application.ports import DraftStore, ScoreUoW, ScoreUoWFactory
from piano_app.application.ports.score.draft_store import DraftNotFoundError, VersionedDraftDocument
from piano_app.application.ports.score.score_repository import (
    ScoreNotFoundError,
    ScoreVersionClashError,
)
from piano_app.domain.score import Score, ScoreMeta


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
            # decide from a locked snapshot, then write inside the same
            # transaction — otherwise the state the decision rests on can move
            # between the check and the overwrite
            await self._ensure_owned_by(
                uow=uow, score_id=versioned.ref_score_id, actor_id=author_id
            )

            try:
                await uow.score_repository.update_content(
                    score_id=versioned.ref_score_id, document=versioned.document
                )
            except ScoreNotFoundError as error:
                raise MissingScoreError(score_id=error.score_id) from error
            except ScoreVersionClashError as error:
                raise AppScoreVersionClashError(
                    score_id=error.score_id, version=error.version
                ) from error
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
            # The new score's document is always a legitimate copy of the
            # draft's content — reading it was already settled when the draft
            # was created, no further permission needed for that. What CAN be
            # refused is the LINEAGE CLAIM: recording derived_from as a frozen
            # (authorless) score. So a frozen parent doesn't reject the save —
            # it only loses its "derived from" link, same as a from-scratch
            # draft never had one. Branching is not owner-gated either way:
            # anyone may derive their own version of a score they can see.
            derived_from_id: str | None = versioned.ref_score_id
            if derived_from_id is not None:
                parent: ScoreMeta | None = await uow.score_repository.get_meta(
                    score_id=derived_from_id
                )
                if parent is None:
                    raise MissingScoreError(score_id=derived_from_id)
                if parent.is_frozen:
                    derived_from_id = None

            created: Score = await uow.score_repository.create(
                title=command.title,
                author_id=author_id,
                composer=command.composer,
                derived_from_id=derived_from_id,
                document=versioned.document,
                is_public=command.is_public,
            )
            await uow.commit()

        return created.id

    async def _ensure_owned_by(self, *, uow: ScoreUoW, score_id: str, actor_id: str) -> None:
        """Identity check — the application layer's half of the decision, and
        where an admin override would be added.

        No frozen-state check here: a frozen score has no author, so no actor
        can match it and this check already refuses everyone. A caller who isn't
        the author never learns whether a private score exists — not-owned is
        only distinguishable from not-found once the score is public anyway."""
        meta: ScoreMeta | None = await uow.score_repository.get_meta_for_update(score_id=score_id)
        if meta is None:
            raise MissingScoreError(score_id=score_id)

        if meta.author_id != actor_id:
            if not meta.is_public:
                raise MissingScoreError(score_id=score_id)

            raise AppScoreNotOwnedError(score_id=score_id)
