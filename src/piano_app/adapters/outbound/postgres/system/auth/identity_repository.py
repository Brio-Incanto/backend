from sqlalchemy import ScalarResult, Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from piano_app.adapters.outbound.postgres.system.schema import UserIdentityModel, UserModel
from piano_app.application.ports.auth.external_identity_verifier import VerifiedIdentity
from piano_app.application.ports.auth.identity_repository import (
    IdentityLinkConflictError,
    UsernameAlreadyExistsError,
    UserProfile,
)


class PostgresIdentityRepository:
    def __init__(
        self,
        *,
        session: AsyncSession,
    ) -> None:
        self._session: AsyncSession = session

    async def create_user(self, *, username: str) -> UserProfile:
        user: UserModel = UserModel(username=username)
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise UsernameAlreadyExistsError(username=username) from error

        return UserProfile(user_id=user.id, username=user.username)

    async def add_identity(self, *, user_id: str, identity: VerifiedIdentity) -> None:
        user_identity: UserIdentityModel = UserIdentityModel(
            authority=identity.authority,
            subject=identity.subject,
            user_id=user_id,
        )
        self._session.add(user_identity)
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise IdentityLinkConflictError from error

    async def find_user_id(self, *, identity: VerifiedIdentity) -> str | None:
        statement: Select[tuple[str]] = select(UserIdentityModel.user_id).where(
            UserIdentityModel.authority == identity.authority,
            UserIdentityModel.subject == identity.subject,
        )
        result: ScalarResult[str] = await self._session.scalars(statement)

        return result.one_or_none()

    async def find_user(self, *, user_id: str) -> UserProfile | None:
        statement: Select[tuple[UserModel]] = select(UserModel).where(UserModel.id == user_id)
        result: ScalarResult[UserModel] = await self._session.scalars(statement)
        user: UserModel | None = result.one_or_none()

        if user is None:
            return None

        return UserProfile(user_id=user.id, username=user.username)
