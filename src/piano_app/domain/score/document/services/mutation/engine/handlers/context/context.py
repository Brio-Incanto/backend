from piano_app.domain.score.document.models.context import Context
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    DeleteContextAction,
)


class DeleteContextHandler:
    """Detaches a context from its anchor(s)."""

    def handle(
        self,
        *,
        action: DeleteContextAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        context: Context = action.target
        context.detach(sink=sink)
        return None
