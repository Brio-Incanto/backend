from piano_app.domain.score.document.models.context import Context
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    DeleteContextAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.context import (
    DeleteContextRequest,
)


class DeleteContextAnalyzer:
    """Decides direct deletion of a context because it owns no child entities."""

    def analyze(
        self,
        *,
        request: DeleteContextRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        context: Context = request.target

        buffer.incorporate(item=DeleteContextAction(target=context))

        return buffer
