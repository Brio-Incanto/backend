from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.relations.base import Relation
from piano_app.domain.score.services.mutation.instructions.actions.relation import (
    DeleteRelationAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class DeleteRelationHandler:
    """Detaches a relation from its peers."""

    def handle(
        self,
        *,
        action: DeleteRelationAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        relation: Relation = action.target
        relation.detach(sink=sink)
        return None
