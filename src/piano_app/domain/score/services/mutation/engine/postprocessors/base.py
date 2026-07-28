from collections.abc import Sequence
from typing import Protocol

from piano_app.domain.score.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)


class PlanPostprocessor(Protocol):
    def search_fixes(
        self,
        *,
        planned_actions: list[MutationAction],
    ) -> Sequence[MutationRequest]: ...
