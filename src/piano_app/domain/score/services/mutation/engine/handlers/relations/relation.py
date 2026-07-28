from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.relations.base import Relation
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.relations.relation import (
    DeleteRelationAction,
)


class DeleteRelationHandler(MutationHandler[DeleteRelationAction]):
    """Detaches a relation from its peers."""

    def handle(
        self,
        *,
        action: DeleteRelationAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        relation: Relation = action.target
        relation.detach(sink=sink)
        return None
