from typing import Any

from piano_app.domain.score.services.mutation.instructions import MutationAction, MutationRequest
from piano_app.domain.score.services.mutation.engine.analyzers.base import (
    MutationAnalyzer,
)
from piano_app.domain.score.services.mutation.engine.handlers import MutationHandler


class MutationAnalyzerRegistry:
    """Maps a concrete request type to the analyzer that is responsible for it."""

    def __init__(self) -> None:
        self._analyzers: dict[type[MutationRequest], MutationAnalyzer[Any]] = {}

    def register(
        self,
        *,
        request_type: type[MutationRequest],
        analyzer: MutationAnalyzer[Any],
    ) -> None:
        self._analyzers[request_type] = analyzer

    def get(self, *, request_type: type[MutationRequest]) -> MutationAnalyzer[Any]:
        return self._analyzers[request_type]


class MutationHandlerRegistry:
    """Maps a concrete action type to the handler that executes it."""

    def __init__(self) -> None:
        self._handlers: dict[type[MutationAction], MutationHandler[Any]] = {}

    def register(
        self,
        *,
        action_type: type[MutationAction],
        handler: MutationHandler[Any],
    ) -> None:
        self._handlers[action_type] = handler

    def get(self, *, action_type: type[MutationAction]) -> MutationHandler[Any]:
        return self._handlers[action_type]
