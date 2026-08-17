from datetime import timedelta
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .identity_repository import PostgresIdentityRepository
from .session_repository import PostgresRefreshSessionRepository


class PostgresAuthUoW:
    def __init__(
        self,
        *,
        session: AsyncSession,
        refresh_token_ttl: timedelta,
    ) -> None:
        self._session: AsyncSession = session

        self._identity_repository: PostgresIdentityRepository = PostgresIdentityRepository(
            session=self._session,
        )
        self._refresh_session_repository: PostgresRefreshSessionRepository = (
            PostgresRefreshSessionRepository(
                session=self._session,
                ttl=refresh_token_ttl,
            )
        )

    @property
    def identity_repository(self) -> PostgresIdentityRepository:
        return self._identity_repository

    @property
    def refresh_session_repository(self) -> PostgresRefreshSessionRepository:
        return self._refresh_session_repository

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


class PostgresAuthUoWFactory:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        refresh_token_ttl: timedelta,
    ) -> None:
        self._session_factory: async_sessionmaker[AsyncSession] = session_factory
        self._refresh_token_ttl: timedelta = refresh_token_ttl

    def __call__(
        self,
    ) -> PostgresAuthUoW:
        return PostgresAuthUoW(
            session=self._session_factory(),
            refresh_token_ttl=self._refresh_token_ttl,
        )
