from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from .score_repository import ScoreRepository


class ScoreUoW(Protocol):
    @property
    def score_repository(self) -> ScoreRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


type ScoreUoWFactory = Callable[[], ScoreUoW]
