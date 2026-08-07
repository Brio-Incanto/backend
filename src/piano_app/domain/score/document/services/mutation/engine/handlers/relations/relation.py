from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.relations import Relation
from piano_app.domain.score.document.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.document.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.document.services.mutation.instructions.actions.relations import (
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
