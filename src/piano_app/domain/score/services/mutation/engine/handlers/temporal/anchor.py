from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.structural import TemporalAnchor
from piano_app.domain.score.services.mutation.instructions.actions.temporal.anchor import (
    CreateTemporalAnchorAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class CreateTemporalAnchorHandler:
    """Creates a temporal anchor in its measure."""

    def handle(
        self,
        *,
        action: CreateTemporalAnchorAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        anchor: TemporalAnchor = TemporalAnchor.create(
            position=action.position,
            measure=action.measure,
            sink=sink,
        )
        return anchor
