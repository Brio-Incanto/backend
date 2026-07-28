from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions.base import (
    MutationInstruction,
)
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationAction(MutationInstruction):
    """Marker base for terminal plan instructions.

    Actions are dumb data carriers: input fields hold either existing entities
    or ``ResultRef`` placeholders, and output refs name the entities the action
    will produce. All behaviour lives in the matching handler, dispatched by
    the action's concrete type.
    """

    @property
    def produced_ref(self) -> ResultRef[Any] | None:
        """The ref to the entity produced by this action. None means no output."""
        raise NotImplementedError

    @property
    def identity_key(self) -> tuple[type[ScoreEntity], Hashable] | None:
        """The key that gives an entity unique identity for deduplication.
        None means that an entity is always emitted (no deduplication).
        """
        return None


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMutationAction[T: ScoreEntity](MutationAction):
    out: ResultRef[T] = field(default_factory=ResultRef)

    @property
    def produced_ref(self) -> ResultRef[T]:
        """The ref to the entity produced by this action."""
        return self.out


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteMutationAction[T: ScoreEntity](MutationAction):
    # A delete always targets a live entity: execution is immediate, so anything
    # deletable already exists (never a ResultRef) — no Bound, no resolve.
    target: T

    @property
    def produced_ref(self) -> None:
        """No output for delete actions."""
        return None
