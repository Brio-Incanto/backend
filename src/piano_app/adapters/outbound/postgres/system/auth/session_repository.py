import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import ScalarResult, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import Delete, ReturningUpdate

from piano_app.adapters.outbound.postgres.system.schema import AuthSessionORM
from piano_app.application.ports.auth.refresh_session_repository import (
    RotatedRefreshSession,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class _RefreshCredential:
    _session_id: str
    _secret: str

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def secret(self) -> str:
        return self._secret

    @classmethod
    def create(cls, *, session_id: str, secret: str) -> _RefreshCredential:
        return cls(_session_id=session_id, _secret=secret)

    @classmethod
    def parse(cls, credential: str) -> _RefreshCredential:
        session_id: str
        separator: str
        secret: str
        session_id, separator, secret = credential.partition(".")
        if not session_id or not separator or not secret:
            raise ValueError("Malformed refresh credential.")

        return cls(_session_id=session_id, _secret=secret)

    def __str__(self) -> str:
        return f"{self._session_id}.{self._secret}"


class PostgresRefreshSessionRepository:
    _TOKEN_ENTROPY_BYTES: Final[int] = 32

    def __init__(
        self,
        *,
        session: AsyncSession,
        ttl: timedelta,
    ) -> None:
        self._session: AsyncSession = session
        self._ttl: timedelta = ttl

    async def create(self, *, user_id: str) -> str:
        secret: str = secrets.token_urlsafe(self._TOKEN_ENTROPY_BYTES)

        orm: AuthSessionORM = AuthSessionORM(
            user_id=user_id,
            refresh_token_hash=self._hash(secret=secret),
            expires_at=datetime.now(UTC) + self._ttl,
        )
        self._session.add(orm)
        await self._session.flush()
        session_id: str = orm.id

        return str(_RefreshCredential.create(session_id=session_id, secret=secret))

    async def rotate(self, *, credential: str) -> RotatedRefreshSession | None:
        try:
            old_credential: _RefreshCredential = _RefreshCredential.parse(credential=credential)
        except ValueError:
            # malformed, same as "not found" for the caller — not this port's
            # own error escaping unhandled past the adapter
            return None
        new_secret: str = secrets.token_urlsafe(self._TOKEN_ENTROPY_BYTES)

        statement: ReturningUpdate[tuple[str]] = (
            update(AuthSessionORM)
            .where(
                AuthSessionORM.id == old_credential.session_id,
                AuthSessionORM.refresh_token_hash == self._hash(secret=old_credential.secret),
                AuthSessionORM.expires_at > datetime.now(UTC),
            )
            .values(
                refresh_token_hash=self._hash(secret=new_secret),
                expires_at=datetime.now(UTC) + self._ttl,
            )
            .returning(AuthSessionORM.user_id)
        )

        result: ScalarResult[str] = await self._session.scalars(statement)
        user_id: str | None = result.one_or_none()

        # if the token has expired or is invalid, then the user_id will be None
        if user_id is None:
            return None

        return RotatedRefreshSession(
            user_id=user_id,
            credential=str(
                _RefreshCredential.create(session_id=old_credential.session_id, secret=new_secret)
            ),
        )

    async def revoke(self, *, credential: str) -> None:
        try:
            cred: _RefreshCredential = _RefreshCredential.parse(credential=credential)
        except ValueError:
            return

        statement: Delete = delete(AuthSessionORM).where(
            AuthSessionORM.id == cred.session_id,
            AuthSessionORM.refresh_token_hash == self._hash(secret=cred.secret),
        )
        await self._session.execute(statement)

    @staticmethod
    def _hash(*, secret: str) -> bytes:
        return hashlib.sha256(secret.encode()).digest()
