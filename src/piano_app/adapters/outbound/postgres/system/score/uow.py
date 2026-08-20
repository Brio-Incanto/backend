from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec

from .author_repository import PostgresAuthorRepository
from .catalog_query import PostgresScoreCatalogQuery
from .score_repository import PostgresScoreRepository


class PostgresScoreUoW:
    def __init__(
        self,
        *,
        session: AsyncSession,
        codec: ScoreDocumentCodec,
    ) -> None:
        self._session: AsyncSession = session
        self._codec: ScoreDocumentCodec = codec

        self._score_repository: PostgresScoreRepository = PostgresScoreRepository(
            session=self._session,
            codec=self._codec,
        )
        self._catalog_query: PostgresScoreCatalogQuery = PostgresScoreCatalogQuery(
            session=self._session,
        )
        self._author_repository: PostgresAuthorRepository = PostgresAuthorRepository(
            session=self._session,
        )

    @property
    def score_repository(self) -> PostgresScoreRepository:
        return self._score_repository

    @property
    def catalog_query(self) -> PostgresScoreCatalogQuery:
        return self._catalog_query

    @property
    def author_repository(self) -> PostgresAuthorRepository:
        return self._author_repository

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class PostgresScoreUoWFactory:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        codec: ScoreDocumentCodec,
    ) -> None:
        self._session_factory: async_sessionmaker[AsyncSession] = session_factory
        self._codec: ScoreDocumentCodec = codec

    def __call__(self) -> PostgresScoreUoW:
        return PostgresScoreUoW(
            session=self._session_factory(),
            codec=self._codec,
        )
