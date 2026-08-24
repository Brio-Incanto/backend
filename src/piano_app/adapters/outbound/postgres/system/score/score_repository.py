from typing import Any

from sqlalchemy import Result, Row, ScalarResult, Select, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate

from piano_app.adapters.outbound.postgres.system.schema import ScoreContentModel, ScoreMetaModel
from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.application.ports.score.score_repository import (
    ScoreRepositoryNotFoundError,
    ScoreRepositoryVersionConflictError,
)
from piano_app.domain.score import Score, ScoreMeta
from piano_app.domain.score.document import ScoreDocument


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

    async def get(self, *, score_id: str) -> Score | None:
        # get with the lattest version by default
        statement: Select[tuple[ScoreMetaModel, ScoreContentModel]] = (
            select(ScoreMetaModel, ScoreContentModel)
            .join(ScoreContentModel, ScoreContentModel.score_id == ScoreMetaModel.id)
            .where(ScoreMetaModel.id == score_id)
            .order_by(ScoreContentModel.version.desc())
            .limit(1)
        )
        result: Result[tuple[ScoreMetaModel, ScoreContentModel]] = await self._session.execute(
            statement
        )
        row: Row[tuple[ScoreMetaModel, ScoreContentModel]] | None = result.one_or_none()

        if row is None:
            return None

        return self._to_domain(
            score_model=row[0],
            content_model=row[1],
        )

    async def get_meta(self, *, score_id: str) -> ScoreMeta | None:
        statement: Select[tuple[ScoreMetaModel]] = select(ScoreMetaModel).where(
            ScoreMetaModel.id == score_id
        )

        result: ScalarResult[ScoreMetaModel] = await self._session.scalars(statement)
        score_model: ScoreMetaModel | None = result.one_or_none()

        if score_model is None:
            return None

        return self._to_meta(score_model=score_model)

    async def exists(self, *, score_id: str) -> bool:
        statement: Select[tuple[bool]] = select(
            select(ScoreMetaModel.id).where(ScoreMetaModel.id == score_id).exists()
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
        score_model: ScoreMetaModel = ScoreMetaModel(
            title=title,
            author_id=author_id,
            composer=composer,
            derived_from_id=derived_from_id,
            is_public=is_public,
        )
        self._session.add(score_model)
        await self._session.flush()

        content_model: ScoreContentModel = ScoreContentModel(
            score_id=score_model.id,
            version=1,
            document=self._codec.serialize(document),
        )
        self._session.add(content_model)
        await self._session.flush()

        return self._to_domain(
            score_model=score_model,
            content_model=content_model,
        )

    async def update_content(self, *, score_id: str, document: ScoreDocument) -> None:
        score_model: ScoreMetaModel | None = await self._session.get(ScoreMetaModel, score_id)
        if score_model is None:
            raise ScoreRepositoryNotFoundError(score_id=score_id)

        statement: Select[tuple[ScoreContentModel]] = (
            select(ScoreContentModel)
            .where(ScoreContentModel.score_id == score_id)
            .order_by(ScoreContentModel.version.desc())
            .limit(1)
        )
        result: ScalarResult[ScoreContentModel] = await self._session.scalars(statement)
        current_content: ScoreContentModel | None = result.one_or_none()

        if current_content is None:
            raise RuntimeError(f"Score {score_id!r} has no content.")

        # increment version
        content_model: ScoreContentModel = ScoreContentModel(
            score_id=score_id,
            version=current_content.version + 1,
            document=self._codec.serialize(document),
        )
        self._session.add(content_model)

        # score existence is already checked, so the issue here is the unique constraint violation
        try:
            await self._session.flush()
        except IntegrityError:
            raise ScoreRepositoryVersionConflictError(
                score_id=score_id, version=content_model.version
            ) from None

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
            update(ScoreMetaModel)
            .where(ScoreMetaModel.id == score_id)
            .values(**values)
            .returning(ScoreMetaModel.id)
        )
        result: ScalarResult[str] = await self._session.scalars(statement)

        if result.one_or_none() is None:
            raise ScoreRepositoryNotFoundError(score_id=score_id)

    @staticmethod
    def _to_meta(*, score_model: ScoreMetaModel) -> ScoreMeta:
        return ScoreMeta(
            id=score_model.id,
            title=score_model.title,
            author_id=score_model.author_id,
            composer=score_model.composer,
            derived_from_id=score_model.derived_from_id,
            is_public=score_model.is_public,
            created_at=score_model.created_at,
            updated_at=score_model.updated_at,
        )

    def _to_domain(
        self,
        *,
        score_model: ScoreMetaModel,
        content_model: ScoreContentModel,
    ) -> Score:
        return Score(
            meta=self._to_meta(score_model=score_model),
            document=self._codec.deserialize(content_model.document),
        )
