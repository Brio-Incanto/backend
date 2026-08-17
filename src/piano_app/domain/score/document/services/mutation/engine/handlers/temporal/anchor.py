from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.temporal import (
    CreateTemporalAnchorAction,
    DeleteTemporalAnchorAction,
)


class CreateTemporalAnchorHandler:
    """Creates a temporal anchor in its measure."""

    def handle(
        self,
        *,
        action: CreateTemporalAnchorAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> TemporalAnchor:
        anchor: TemporalAnchor = TemporalAnchor.create(
            position=action.position,
            measure=action.measure,
            sink=sink,
        )
        return anchor


class DeleteTemporalAnchorHandler:
    """Detaches a temporal anchor from its measure."""

    def handle(
        self,
        *,
        action: DeleteTemporalAnchorAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        anchor: TemporalAnchor = action.target
        anchor.detach(sink=sink)
        return None
