from dataclasses import dataclass

from piano_app.domain.score.models.relations.base import Relation
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRelationRequest(DeleteMutationRequest[Relation]):
    """A request to delete a relation."""
