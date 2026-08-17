from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from .identity_repository import IdentityRepository
from .refresh_session_repository import RefreshSessionRepository


class AuthUow(Protocol):
    @property
    def refresh_session_repository(self) -> RefreshSessionRepository: ...

    @property
    def identity_repository(self) -> IdentityRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


type AuthUoWFactory = Callable[[], AuthUow]
