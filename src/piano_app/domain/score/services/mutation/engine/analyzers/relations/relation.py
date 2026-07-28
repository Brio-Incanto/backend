from piano_app.domain.score.services.mutation.engine import EmitBuffer, PlanningScope
from piano_app.domain.score.services.mutation.instructions.actions import (
    DeleteRelationAction,
)
from piano_app.domain.score.services.mutation.instructions.requests.relations.relation import (
    DeleteRelationRequest,
)


class DeleteRelationAnalyzer:
    """A relation owns nothing, so its delete is a single action — no cascade."""

    def analyze(
        self,
        *,
        request: DeleteRelationRequest,
        scope: PlanningScope,
    ) -> EmitBuffer:
        buffer: EmitBuffer = scope.create_buffer()
        buffer.incorporate_delete(item=DeleteRelationAction(target=request.relation))
        return buffer
