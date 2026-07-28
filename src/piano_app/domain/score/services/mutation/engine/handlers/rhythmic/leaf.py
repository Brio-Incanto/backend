from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.structural import TemporalAnchor
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)
from piano_app.domain.score.services.mutation.instructions.actions.rhythmic.leaf import (
    CreateLeafAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class CreateLeafHandler:
    """Creates a leaf rhythmic container, at its anchor and inside its optional
    parent group (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateLeafAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        anchor: TemporalAnchor = resolve(action.anchor)
        parent: RhythmicContainerParent = resolve(action.parent)

        leaf: LeafRhythmicContainer = LeafRhythmicContainer.create(
            size=action.size,
            anchor=anchor,
            parent=parent,
            sink=sink,
        )
        return leaf
