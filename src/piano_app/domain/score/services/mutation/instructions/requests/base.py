from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions.base import (
    MutationInstruction,
)
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationRequest(MutationInstruction):
    @property
    def produced_ref(self) -> ResultRef[Any] | None:
        """The reference to be passed to the action that is produced by this request."""
        return None

    @property
    def identity_key(self) -> tuple[type[ScoreEntity], Hashable] | None:
        """The key that gives an entity unique identity for deduplication.
        None means that an entity is always emitted (no deduplication).
        """
        return None
