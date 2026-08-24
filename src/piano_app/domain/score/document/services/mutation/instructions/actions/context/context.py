from dataclasses import dataclass

from piano_app.domain.score.document.models.context import Context
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    DeleteMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteContextAction(DeleteMutationAction[Context]):
    """Deletes a context."""
