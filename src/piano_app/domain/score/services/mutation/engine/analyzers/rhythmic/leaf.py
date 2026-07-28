from piano_app.domain.score.services.mutation.instructions.requests.rhythmic.leaf import (
    CreateLeafRhythmicContainerRequest,
)
from piano_app.domain.score.services.mutation.engine.scope import (
    EmitBuffer,
    PlanningScope,
)


class CreateLeafAnalyzer:
    """Leaf level: the spatial decision (how inserting a leaf of size S affects
    neighbours, who to delete) plus anchor find-or-create.

    TODO: not implemented — emits the leaf action and resolves the anchor via
     ``scope.emit_create`` (find-or-create by position), raising on unsupported
     insertions (cross-measure, front-trim). See plan D.
    """

    def analyze(
        self,
        *,
        request: CreateLeafRhythmicContainerRequest,
        scope: PlanningScope,
    ) -> EmitBuffer:
        raise NotImplementedError
