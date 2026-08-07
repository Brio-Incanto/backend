from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.models.structural.rhythm import (
    LeafRhythmicContainer,
    RhythmicContainerParent,
)
from piano_app.domain.score.document.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.document.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.document.services.mutation.instructions.actions.rhythmic import (
    CreateLeafAction,
    DeleteLeafAction,
)


class CreateLeafHandler(MutationHandler[CreateLeafAction]):
    """Creates a leaf rhythmic container, at its anchor and inside its optional
    parent group (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateLeafAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> LeafRhythmicContainer:
        anchor: TemporalAnchor = resolve(action.anchor)
        parent: RhythmicContainerParent = resolve(action.parent)

        leaf: LeafRhythmicContainer = LeafRhythmicContainer.create(
            parent=parent,
            anchor=anchor,
            size=action.size,
            sink=sink,
        )
        return leaf


class DeleteLeafHandler(MutationHandler[DeleteLeafAction]):
    """Detaches a leaf from its parent scope."""

    def handle(
        self,
        *,
        action: DeleteLeafAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        leaf: LeafRhythmicContainer = action.target
        leaf.detach(sink=sink)
        return None
