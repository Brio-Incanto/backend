from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.rhythmic import (
    DeleteRhythmicGroupAction,
)


class DeleteRhythmicGroupHandler:
    """Detaches a rhythmic group from its parent scope."""

    def handle(
        self,
        *,
        action: DeleteRhythmicGroupAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        group: GroupRhythmicContainer = action.target
        group.detach(sink=sink)
        return None
