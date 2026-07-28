from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.structural import TemporalAnchor
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.temporal.anchor import (
    CreateTemporalAnchorAction,
    DeleteTemporalAnchorAction,
)


class CreateTemporalAnchorHandler(MutationHandler[CreateTemporalAnchorAction]):
    """Creates a temporal anchor in its measure."""

    def handle(
        self,
        *,
        action: CreateTemporalAnchorAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> TemporalAnchor:
        anchor: TemporalAnchor = TemporalAnchor.create(
            position=action.position,
            measure=action.measure,
            sink=sink,
        )
        return anchor


class DeleteTemporalAnchorHandler(MutationHandler[DeleteTemporalAnchorAction]):
    """Detaches a temporal anchor from its measure."""

    def handle(
        self,
        *,
        action: DeleteTemporalAnchorAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        anchor: TemporalAnchor = action.target
        anchor.detach(sink=sink)
        return None
