from dataclasses import dataclass
from typing import Any

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef
from piano_app.domain.shared.abstract import abstract


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class MutationRequest:
    """Role base: a work item expanded by its analyzer."""

    @property
    def produced_ref(self) -> ResultRef[Any] | None:
        raise NotImplementedError


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMutationRequest[T: ScoreEntity](MutationRequest):
    """A request that creates an entity, published through ``out``."""

    out: ResultRef[T]

    @property
    def produced_ref(self) -> ResultRef[T]:
        return self.out


@abstract
@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteMutationRequest[T: ScoreEntity](MutationRequest):
    """A request that removes an existing ``target``."""

    target: T

    @property
    def produced_ref(self) -> None:
        return None
