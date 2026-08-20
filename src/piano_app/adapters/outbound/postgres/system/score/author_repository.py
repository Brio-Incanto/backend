from sqlalchemy import ScalarResult, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from piano_app.adapters.outbound.postgres.system.schema import UserORM
from piano_app.application.ports.score.author_repository import AuthorProfile


class PostgresAuthorRepository:
    def __init__(self, *, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def get(self, *, author_id: str) -> AuthorProfile | None:
        statement: Select[tuple[UserORM]] = select(UserORM).where(UserORM.id == author_id)
        result: ScalarResult[UserORM] = await self._session.scalars(statement)
        user: UserORM | None = result.one_or_none()

        if user is None:
            return None

        return AuthorProfile(id=user.id, username=user.username, bio=user.bio)
