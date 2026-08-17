from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from piano_app.application.errors import InvalidCursorError as AppInvalidCursorError
from piano_app.application.errors import MissingScoreError
from piano_app.application.ports import (
    AuthorProfile,
    InvalidCursorError,
    Page,
    ScoreMetaItem,
    ScoreUoWFactory,
)
from piano_app.application.use_cases.score.shared import ScoreView
from piano_app.domain.score import Score


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreItem:
    id: str
    title: str
    author_id: str | None
    author_name: str | None = None
    composer: str | None = None
    derived_from_id: str | None = None
    is_public: bool = False
    document: ScoreView
    created_at: datetime
    updated_at: datetime


class ScoreCatalogService:
    """Read-side orchestration for browsing the score catalog. Reads go through a
    ``ScoreUoW`` (rollback-on-exit is a no-op for a read, no commit needed)."""

    def __init__(self, *, score_uow_factory: ScoreUoWFactory) -> None:
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def search(
        self,
        *,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        async with self._score_uow_factory() as uow:
            try:
                return await uow.catalog_query.search(query=query, limit=limit, cursor=cursor)
            except InvalidCursorError as error:
                raise AppInvalidCursorError from error

    async def search_mine(
        self,
        *,
        viewer_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        async with self._score_uow_factory() as uow:
            try:
                return await uow.catalog_query.search_mine(
                    viewer_id=viewer_id, query=query, limit=limit, cursor=cursor
                )
            except InvalidCursorError as error:
                raise AppInvalidCursorError from error

    async def get_score_branches(
        self, *, score_id: str, viewer_id: str | None
    ) -> Sequence[ScoreMetaItem]:
        async with self._score_uow_factory() as uow:
            return await uow.catalog_query.get_score_branches(
                score_id=score_id, viewer_id=viewer_id
            )

    async def get_score(self, *, score_id: str, viewer_id: str | None) -> ScoreItem:
        async with self._score_uow_factory() as uow:
            score: Score | None = await uow.score_repository.get(
                score_id=score_id, viewer_id=viewer_id
            )
            if score is None:
                raise MissingScoreError(score_id=score_id)

            author_name: str | None = None
            if score.author_id is not None:
                author: AuthorProfile | None = await uow.author_repository.get(
                    author_id=score.author_id
                )
                # a missing author (deleted account) just means no name to show —
                # not a reason to fail the whole score fetch
                author_name = author.username if author is not None else None

            return ScoreItem(
                id=score.id,
                title=score.title,
                author_id=score.author_id,
                author_name=author_name,
                composer=score.composer,
                derived_from_id=score.derived_from_id,
                is_public=score.is_public,
                document=ScoreView(document=score.document),
                created_at=score.created_at,
                updated_at=score.updated_at,
            )
