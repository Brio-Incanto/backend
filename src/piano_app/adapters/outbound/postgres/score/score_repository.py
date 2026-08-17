from typing import Any

from sqlalchemy import Result, Row, ScalarResult, Select, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate

from piano_app.adapters.outbound.postgres.schema.core import ScoreContentORM, ScoreMetaORM
from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.application.ports.score.score_repository import (
    ScoreNotFoundError,
    ScoreVersionClashError,
)
from piano_app.domain.score import Score, ScoreMeta
from piano_app.domain.score.document import ScoreDocument

from .helpers.visibility import is_readable_by


class PostgresScoreRepository:
    """Implements 'ScoreRepository' using Postgres."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        codec: ScoreDocumentCodec,
    ) -> None:
        self._session: AsyncSession = session
        self._codec: ScoreDocumentCodec = codec

    async def get(self, *, score_id: str, viewer_id: str | None) -> Score | None:
        # get with the lattest version by default
        statement: Select[tuple[ScoreMetaORM, ScoreContentORM]] = (
            select(ScoreMetaORM, ScoreContentORM)
            .join(ScoreContentORM, ScoreContentORM.score_id == ScoreMetaORM.id)
            .where(
                ScoreMetaORM.id == score_id,
                is_readable_by(viewer_id=viewer_id),
            )
            .order_by(ScoreContentORM.version.desc())
            .limit(1)
        )
        result: Result[tuple[ScoreMetaORM, ScoreContentORM]] = await self._session.execute(
            statement
        )
        row: Row[tuple[ScoreMetaORM, ScoreContentORM]] | None = result.one_or_none()

        if row is None:
            return None

        return self._to_domain(
            score_orm=row[0],
            content_orm=row[1],
        )

    async def get_meta(self, *, score_id: str) -> ScoreMeta | None:
        return await self._load_meta(score_id=score_id, lock=False)

    async def get_meta_for_update(self, *, score_id: str) -> ScoreMeta | None:
        return await self._load_meta(score_id=score_id, lock=True)

    async def _load_meta(self, *, score_id: str, lock: bool) -> ScoreMeta | None:
        statement: Select[tuple[ScoreMetaORM]] = select(ScoreMetaORM).where(
            ScoreMetaORM.id == score_id
        )
        if lock:
            # holds until the surrounding uow commits/rolls back, so a decision
            # taken from this snapshot still holds when the write lands
            statement = statement.with_for_update()

        result: ScalarResult[ScoreMetaORM] = await self._session.scalars(statement)
        score_orm: ScoreMetaORM | None = result.one_or_none()

        return None if score_orm is None else self._to_meta(score_orm=score_orm)

    async def exists(self, *, score_id: str) -> bool:
        statement: Select[tuple[bool]] = select(
            select(ScoreMetaORM.id).where(ScoreMetaORM.id == score_id).exists()
        )

        result: Result[tuple[bool]] = await self._session.execute(statement)

        return result.scalar_one()

    async def create(
        self,
        *,
        title: str,
        author_id: str,
        composer: str | None = None,
        derived_from_id: str | None = None,
        document: ScoreDocument,
        is_public: bool = False,
    ) -> Score:
        score_orm: ScoreMetaORM = ScoreMetaORM(
            title=title,
            author_id=author_id,
            composer=composer,
            derived_from_id=derived_from_id,
            is_public=is_public,
        )
        self._session.add(score_orm)
        await self._session.flush()

        content_orm: ScoreContentORM = ScoreContentORM(
            score_id=score_orm.id,
            version=1,
            document=self._codec.serialize(document),
        )
        self._session.add(content_orm)
        await self._session.flush()

        return self._to_domain(
            score_orm=score_orm,
            content_orm=content_orm,
        )

    async def update_content(self, *, score_id: str, document: ScoreDocument) -> None:
        score_orm: ScoreMetaORM | None = await self._session.get(ScoreMetaORM, score_id)
        if score_orm is None:
            raise ScoreNotFoundError(score_id=score_id)

        statement: Select[tuple[ScoreContentORM]] = (
            select(ScoreContentORM)
            .where(ScoreContentORM.score_id == score_id)
            .order_by(ScoreContentORM.version.desc())
            .limit(1)
        )
        result: ScalarResult[ScoreContentORM] = await self._session.scalars(statement)
        current_content: ScoreContentORM | None = result.one_or_none()

        if current_content is None:
            raise RuntimeError(f"Score {score_id!r} has no content.")

        # increment version
        content_orm: ScoreContentORM = ScoreContentORM(
            score_id=score_id,
            version=current_content.version + 1,
            document=self._codec.serialize(document),
        )
        self._session.add(content_orm)

        # score existence is already checked, so the issue here is the unique constraint violation
        try:
            await self._session.flush()
        except IntegrityError:
            raise ScoreVersionClashError(score_id=score_id, version=content_orm.version) from None

    async def set_title(self, *, score_id: str, title: str) -> None:
        await self._write_meta(score_id=score_id, title=title)

    async def set_composer(self, *, score_id: str, composer: str | None) -> None:
        await self._write_meta(score_id=score_id, composer=composer)

    async def set_visibility(self, *, score_id: str, is_public: bool) -> None:
        await self._write_meta(score_id=score_id, is_public=is_public)

    async def _write_meta(self, *, score_id: str, **values: Any) -> None:
        """Unconditional metadata write — whether it is allowed was already
        settled by the caller (see the port). The only failure left here is the
        row having disappeared."""
        statement: ReturningUpdate[tuple[str]] = (
            update(ScoreMetaORM)
            .where(ScoreMetaORM.id == score_id)
            .values(**values)
            .returning(ScoreMetaORM.id)
        )
        result: ScalarResult[str] = await self._session.scalars(statement)

        if result.one_or_none() is None:
            raise ScoreNotFoundError(score_id=score_id)

    @staticmethod
    def _to_meta(*, score_orm: ScoreMetaORM) -> ScoreMeta:
        return ScoreMeta(
            id=score_orm.id,
            title=score_orm.title,
            author_id=score_orm.author_id,
            composer=score_orm.composer,
            derived_from_id=score_orm.derived_from_id,
            is_public=score_orm.is_public,
            created_at=score_orm.created_at,
            updated_at=score_orm.updated_at,
        )

    def _to_domain(
        self,
        *,
        score_orm: ScoreMetaORM,
        content_orm: ScoreContentORM,
    ) -> Score:
        return Score(
            meta=self._to_meta(score_orm=score_orm),
            document=self._codec.deserialize(content_orm.document),
        )
