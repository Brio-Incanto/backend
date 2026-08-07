from sqlalchemy import Exists, Result, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from piano_app.adapters.outbound.postgres.schema import ScoreORM
from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.application.ports.score_repository import ScoreNotFoundError
from piano_app.domain.score import Score
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
        orm: ScoreORM | None = await self._session.get(ScoreORM, score_id)
        return orm.to_domain(codec=self._codec) if orm is not None else None

    async def exists(self, *, score_id: str) -> bool:
        exists_clause: Exists = select(ScoreORM.id).where(ScoreORM.id == score_id).exists()
        statement: Select[tuple[bool]] = select(exists_clause)
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
        orm: ScoreORM = ScoreORM(
            title=title,
            author_id=author_id,
            composer=composer,
            derived_from_id=derived_from_id,
            document=self._codec.serialize(document),
            is_public=is_public,
        )
        self._session.add(orm)
        await self._session.flush()
        return orm.to_domain(codec=self._codec)

    async def update(self, *, score_id: str, document: ScoreDocument) -> None:
        orm: ScoreORM | None = await self._session.get(ScoreORM, score_id)
        if orm is None:
            raise ScoreNotFoundError(score_id=score_id)

        orm.document = self._codec.serialize(document)
        await self._session.flush()
