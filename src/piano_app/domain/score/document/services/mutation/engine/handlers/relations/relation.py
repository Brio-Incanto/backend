from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.relations import Relation
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.relations import (
    DeleteRelationAction,
)


class DeleteRelationHandler:
    """Detaches a relation from its peers."""

    def handle(
        self,
        *,
        action: DeleteRelationAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        relation: Relation = action.target
        relation.detach(sink=sink)
        return None
