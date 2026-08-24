from collections.abc import Sequence
from datetime import datetime
from typing import Final

from sqlalchemy import Result, Row, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from piano_app.adapters.outbound.postgres.system.schema import ScoreMetaModel, UserModel
from piano_app.application.ports.score.catalog_query import ScoreMetaItem
from piano_app.application.ports.shared.pagination import Page

from .helpers.cursor_ordering import CursorOrdering
from .helpers.search import matches
from .helpers.visibility import is_authored_by, is_discoverable, is_readable_by

_NEWEST: Final[CursorOrdering[datetime]] = CursorOrdering.create(
    criterion=ScoreMetaModel.created_at,
    identity=ScoreMetaModel.id,
    descending=True,
    serialize=datetime.isoformat,
    deserialize=datetime.fromisoformat,
)


class PostgresScoreCatalogQuery:
    """Read-side catalog queries over the ``scores`` table. Metadata only — never touches
    ``score_contents.document``.

    Visibility, search and ordering are independent pieces; this class only composes them."""

    def __init__(self, *, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def search(
        self,
        *,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        # discoverable only, no viewer widening
        cursor_ordering: CursorOrdering[datetime] = _NEWEST

        statement: Select[tuple[ScoreMetaModel, str, datetime, str]] = (
            select(
                ScoreMetaModel,
                UserModel.username,
                *cursor_ordering.columns(),
            )
            .join(UserModel, ScoreMetaModel.author_id == UserModel.id)
            .where(
                is_discoverable(),
                matches(query=query),
                cursor_ordering.bounds(cursor=cursor),
            )
            .order_by(*cursor_ordering.clauses())
            .limit(limit + 1)
        )
        result: Result[tuple[ScoreMetaModel, str, datetime, str]] = await self._session.execute(
            statement
        )
        rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = result.all()
        page_rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = rows[:limit]

        next_cursor: str | None = None
        if len(rows) > limit:
            next_cursor = cursor_ordering.cursor_for(
                value=page_rows[-1][-2],
                identity=page_rows[-1][-1],
            )

        return Page(
            items=[self._to_item(score=row[0], author_name=row[1]) for row in page_rows],
            next_cursor=next_cursor,
        )

    # TODO consider returning without author name
    async def search_mine(
        self,
        *,
        viewer_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        cursor_ordering: CursorOrdering[datetime] = _NEWEST

        statement: Select[tuple[ScoreMetaModel, str, datetime, str]] = (
            select(
                ScoreMetaModel,
                UserModel.username,
                *cursor_ordering.columns(),
            )
            .join(UserModel, ScoreMetaModel.author_id == UserModel.id)
            .where(
                is_authored_by(author_id=viewer_id),
                matches(query=query),
                cursor_ordering.bounds(cursor=cursor),
            )
            .order_by(*cursor_ordering.clauses())
            .limit(limit + 1)
        )
        result: Result[tuple[ScoreMetaModel, str, datetime, str]] = await self._session.execute(
            statement
        )
        rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = result.all()
        page_rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = rows[:limit]

        next_cursor: str | None = None
        if len(rows) > limit:
            next_cursor = cursor_ordering.cursor_for(
                value=page_rows[-1][-2],
                identity=page_rows[-1][-1],
            )

        return Page(
            items=[self._to_item(score=row[0], author_name=row[1]) for row in page_rows],
            next_cursor=next_cursor,
        )

    async def search_author_scores(
        self,
        *,
        author_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        cursor_ordering: CursorOrdering[datetime] = _NEWEST

        statement: Select[tuple[ScoreMetaModel, str, datetime, str]] = (
            select(
                ScoreMetaModel,
                UserModel.username,
                *cursor_ordering.columns(),
            )
            .join(UserModel, ScoreMetaModel.author_id == UserModel.id)
            .where(
                is_authored_by(author_id=author_id),
                is_discoverable(),  # author is not none check is excessive
                matches(query=query),
                cursor_ordering.bounds(cursor=cursor),
            )
            .order_by(*cursor_ordering.clauses())
            .limit(limit + 1)
        )
        result: Result[tuple[ScoreMetaModel, str, datetime, str]] = await self._session.execute(
            statement
        )
        rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = result.all()
        page_rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = rows[:limit]

        next_cursor: str | None = None
        if len(rows) > limit:
            next_cursor = cursor_ordering.cursor_for(
                value=page_rows[-1][-2],
                identity=page_rows[-1][-1],
            )

        return Page(
            items=[self._to_item(score=row[0], author_name=row[1]) for row in page_rows],
            next_cursor=next_cursor,
        )

    async def get_score_branches(
        self,
        *,
        score_id: str,
        viewer_id: str | None,
        limit: int,
        cursor: str | None = None,
    ) -> Page[ScoreMetaItem]:
        cursor_ordering: CursorOrdering[datetime] = _NEWEST

        statement: Select[tuple[ScoreMetaModel, str, datetime, str]] = (
            select(
                ScoreMetaModel,
                UserModel.username,
                *cursor_ordering.columns(),
            )
            .join(UserModel, ScoreMetaModel.author_id == UserModel.id)
            .where(
                ScoreMetaModel.derived_from_id == score_id,
                is_readable_by(viewer_id=viewer_id),
                cursor_ordering.bounds(cursor=cursor),
            )
        )
        result: Result[tuple[ScoreMetaModel, str, datetime, str]] = await self._session.execute(
            statement
        )
        rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = result.all()
        page_rows: Sequence[Row[tuple[ScoreMetaModel, str, datetime, str]]] = rows[:limit]

        next_cursor: str | None = None
        if len(rows) > limit:
            next_cursor = cursor_ordering.cursor_for(
                value=page_rows[-1][-2],
                identity=page_rows[-1][-1],
            )

        return Page(
            items=[self._to_item(score=row[0], author_name=row[1]) for row in page_rows],
            next_cursor=next_cursor,
        )

    @staticmethod
    def _to_item(*, score: ScoreMetaModel, author_name: str | None) -> ScoreMetaItem:
        return ScoreMetaItem(
            id=score.id,
            title=score.title,
            composer=score.composer,
            author_id=score.author_id,
            author_name=author_name,
            is_public=score.is_public,
            created_at=score.created_at,
            updated_at=score.updated_at,
        )
