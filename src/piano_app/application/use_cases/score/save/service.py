from piano_app.application.contracts.score import CreateScoreCommand
from piano_app.application.errors import (
    ScoreNotFoundError,
    ScoreVersionConflictError,
)
from piano_app.application.ports import DraftStore, ScoreUoWFactory
from piano_app.application.ports.score import (
    ScoreRepositoryNotFoundError,
    ScoreRepositoryVersionConflictError,
    VersionedDraftDocument,
)
from piano_app.application.use_cases.score.shared import (
    require_accessible_draft,
    require_score_write_access,
)
from piano_app.domain.score import Score, ScoreMeta


class SaveScoreService:
    def __init__(self, *, storage: DraftStore, score_uow_factory: ScoreUoWFactory) -> None:
        self._storage: DraftStore = storage
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def promote(self, *, draft_id: str, actor_id: str) -> str:
        versioned: VersionedDraftDocument = await require_accessible_draft(
            storage=self._storage,
            draft_id=draft_id,
            viewer_id=actor_id,
        )

        if versioned.meta.ref_score_id is None:
            raise ScoreNotFoundError()

        async with self._score_uow_factory() as uow:
            await require_score_write_access(
                score_repository=uow.score_repository,
                score_id=versioned.meta.ref_score_id,
                actor_id=actor_id,
            )

            try:
                await uow.score_repository.update_content(
                    score_id=versioned.meta.ref_score_id,
                    document=versioned.document,
                )
            except ScoreRepositoryNotFoundError as error:
                raise ScoreNotFoundError(score_id=error.score_id) from error
            except ScoreRepositoryVersionConflictError as error:
                raise ScoreVersionConflictError(
                    score_id=error.score_id,
                    version=error.version,
                ) from error

            await uow.commit()

        return versioned.meta.ref_score_id

    async def create_branch(
        self,
        *,
        draft_id: str,
        actor_id: str,
        command: CreateScoreCommand,
    ) -> str:
        versioned: VersionedDraftDocument = await require_accessible_draft(
            storage=self._storage,
            draft_id=draft_id,
            viewer_id=actor_id,
        )

        async with self._score_uow_factory() as uow:
            # The new score's document is always a legitimate copy of the
            # draft's content — reading it was already settled when the draft
            # was created, no further permission needed for that. What CAN be
            # refused is the LINEAGE CLAIM: recording derived_from as a frozen
            # (authorless) score. So a frozen parent doesn't reject the save —
            # it only loses its "derived from" link, same as a from-scratch
            # draft never had one. Branching is not owner-gated either way:
            # anyone may derive their own version of a score they can see.
            derived_from_id: str | None = versioned.meta.ref_score_id
            if derived_from_id is not None:
                parent: ScoreMeta | None = await uow.score_repository.get_meta(
                    score_id=derived_from_id
                )
                if parent is None:
                    raise ScoreNotFoundError(score_id=derived_from_id)
                if parent.is_frozen:
                    derived_from_id = None

            created: Score = await uow.score_repository.create(
                title=command.title,
                author_id=actor_id,
                composer=command.composer,
                derived_from_id=derived_from_id,
                document=versioned.document,
                is_public=command.is_public,
            )
            await uow.commit()

        return created.id
