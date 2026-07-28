from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationInstruction:
    @property
    def produced_ref(self) -> ResultRef[Any] | None:
        raise NotImplementedError

    @property
    def identity_key(self) -> tuple[type[ScoreEntity], Hashable] | None:
        raise NotImplementedError
