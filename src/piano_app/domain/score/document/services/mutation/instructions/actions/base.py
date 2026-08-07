from dataclasses import dataclass
from typing import Any

from piano_app.domain.score.document.models import ScoreEntity
from piano_app.domain.score.document.services.mutation.instructions.refs import ResultRef
from piano_app.domain.shared.abstract import abstract


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class MutationAction:
    """Role base: a terminal work item executed by its handler.

    Actions are dumb data records — inputs hold existing entities or
    ``ResultRef`` placeholders; all behavior lives in the matching handler.
    """

    @property
    def produced_ref(self) -> ResultRef[Any] | None:
        raise NotImplementedError


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMutationAction[T: ScoreEntity](MutationAction):
    """An action that creates an entity, published through ``out``."""

    out: ResultRef[T]

    @property
    def produced_ref(self) -> ResultRef[T]:
        return self.out


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteMutationAction[T: ScoreEntity](MutationAction):
    """An action that removes an existing ``target``."""

    target: T

    @property
    def produced_ref(self) -> None:
        return None
