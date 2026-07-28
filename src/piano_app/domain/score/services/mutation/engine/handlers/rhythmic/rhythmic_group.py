from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.rhythmic.rhythmic_group import (
    DeleteRhythmicGroupAction,
)


class DeleteRhythmicGroupHandler(MutationHandler[DeleteRhythmicGroupAction]):
    """Detaches a rhythmic group from its parent scope."""

    def handle(
        self,
        *,
        action: DeleteRhythmicGroupAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        group: GroupRhythmicContainer = action.target
        group.detach(sink=sink)
        return None
