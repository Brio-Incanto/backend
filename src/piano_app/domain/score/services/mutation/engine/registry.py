from typing import Any

from piano_app.domain.score.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.services.mutation.engine.handlers import MutationHandler
from piano_app.domain.score.services.mutation.instructions import MutationAction, MutationRequest


class MutationAnalyzerRegistry:
    """Maps a concrete request type to the analyzer that is responsible for it."""

    def __init__(self) -> None:
        self._analyzers: dict[type[MutationRequest], MutationAnalyzer[Any]] = {}

    def register[R: MutationRequest](
        self,
        *,
        request_type: type[R],
        analyzer: MutationAnalyzer[R],
    ) -> None:
        self._analyzers[request_type] = analyzer

    def get[R: MutationRequest](self, *, request_type: type[R]) -> MutationAnalyzer[R]:
        return self._analyzers[request_type]


class MutationHandlerRegistry:
    """Maps a concrete action type to the handler that executes it."""

    def __init__(self) -> None:
        self._handlers: dict[type[MutationAction], MutationHandler[Any]] = {}

    def register[A: MutationAction](
        self,
        *,
        action_type: type[A],
        handler: MutationHandler[A],
    ) -> None:
        self._handlers[action_type] = handler

    def get[A: MutationAction](self, *, action_type: type[A]) -> MutationHandler[A]:
        return self._handlers[action_type]
