from dataclasses import dataclass

from piano_app.domain.score.models.relations import Relation

from .base import DeleteMutationAction


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRelationAction(DeleteMutationAction[Relation]):
    """Delete a relation — detaches it from its peers, no cascade."""
