from collections.abc import Sequence

from sqlalchemy import ColumnElement, Label, Result, Row, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from piano_app.adapters.outbound.postgres.schema.core import ScoreMetaORM, UserORM
from piano_app.application.ports.score.catalog_query import ScoreMetaItem
from piano_app.application.ports.shared.pagination import Page

from .helpers.keyset import NEWEST_PAGE, Keyset
from .helpers.search import matches
from .helpers.visibility import is_authored_by, is_discoverable, is_readable_by


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
        return await self._list(
            visibility=is_discoverable(),
            query=query,
            limit=limit,
            cursor=cursor,
            keyset=NEWEST_PAGE,
        )

    async def search_mine(
        self,
        *,
        viewer_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        return await self._list(
            visibility=is_authored_by(author_id=viewer_id),
            query=query,
            limit=limit,
            cursor=cursor,
            keyset=NEWEST_PAGE,
        )

    async def get_score_branches(
        self,
        *,
        score_id: str,
        viewer_id: str | None,
    ) -> Sequence[ScoreMetaItem]:
        statement: Select[tuple[ScoreMetaORM, str]] = (
            select(ScoreMetaORM, UserORM.username)
            .join(UserORM, ScoreMetaORM.author_id == UserORM.id)
            .where(
                ScoreMetaORM.derived_from_id == score_id,
                is_readable_by(viewer_id=viewer_id),
            )
        )
        result: Result[tuple[ScoreMetaORM, str]] = await self._session.execute(statement)

        return [self._to_item(score=row[0], author_name=row[1]) for row in result.all()]

    async def _list[T](
        self,
        *,
        visibility: ColumnElement[bool],
        query: str | None,
        limit: int,
        cursor: str | None,
        keyset: Keyset[T],
    ) -> Page[ScoreMetaItem]:
        """Every paginated listing, differing only in the visibility rule applied to it.

        The criterion is selected alongside the row so the next cursor is minted from the
        value the database actually ordered by."""
        criterion: Label[T] = keyset.order.criterion.label("order_value")

        statement: Select[tuple[ScoreMetaORM, str, T]] = (
            select(ScoreMetaORM, UserORM.username, criterion)
            .join(UserORM, ScoreMetaORM.author_id == UserORM.id)
            .where(
                visibility,
                matches(query=query),
                keyset.seek(cursor=cursor),
            )
            .order_by(*keyset.order.clauses())
            # one extra row tells us whether a further page exists, without a COUNT
            .limit(limit + 1)
        )

        result: Result[tuple[ScoreMetaORM, str, T]] = await self._session.execute(statement)
        rows: Sequence[Row[tuple[ScoreMetaORM, str, T]]] = result.all()
        page_rows: Sequence[Row[tuple[ScoreMetaORM, str, T]]] = rows[:limit]

        next_cursor: str | None = None
        if len(rows) > limit and page_rows:
            # minted from the last row returned, never the extra probe row
            next_cursor = keyset.encode(
                value=page_rows[-1][2],
                identity=page_rows[-1][0].id,
            )

        return Page(
            items=[self._to_item(score=row[0], author_name=row[1]) for row in page_rows],
            next_cursor=next_cursor,
        )

    @staticmethod
    def _to_item(*, score: ScoreMetaORM, author_name: str | None) -> ScoreMetaItem:
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
