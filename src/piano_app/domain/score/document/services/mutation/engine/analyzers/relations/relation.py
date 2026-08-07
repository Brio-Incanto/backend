from piano_app.domain.score.document.models.relations import Relation
from piano_app.domain.score.document.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.relations import (
    DeleteRelationAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.relations import (
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
