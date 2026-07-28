from piano_app.domain.score.models.relations import Relation
from piano_app.domain.score.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.services.mutation.instructions.actions.relations import (
    DeleteRelationAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations.relation import (
    DeleteRelationRequest,
)


class DeleteRelationAnalyzer(MutationAnalyzer[DeleteRelationRequest]):
    """Decides direct deletion of a relation because it owns no child entities."""

    def analyze(
        self,
        *,
        request: DeleteRelationRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        relation: Relation = request.target

        buffer.incorporate(item=DeleteRelationAction(target=relation))

        return buffer
