from dataclasses import dataclass

from piano_app.domain.score.document.models.relations import Relation
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    DeleteMutationAction,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRelationAction(DeleteMutationAction[Relation]):
    """Deletes a relation."""
