from dataclasses import dataclass

from piano_app.domain.score.models.relations.base import Relation

from .base import MutationRequest


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRelationRequest(MutationRequest):
    """Delete a relation — every relation detaches the same way and cascades nothing."""

    relation: Relation
