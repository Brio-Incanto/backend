from piano_app.domain.score.document.models.context import ClefChange
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    CreateClefChangeAction,
)


class CreateClefChangeHandler:
    """Creates a clef change on its anchor (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateClefChangeAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> ClefChange:
        start: TemporalAnchor = resolve(action.start)
        return ClefChange.create(
            start=start,
            staff=action.staff,
            clef=action.clef,
            octave_transposition=action.octave_transposition,
            sink=sink,
        )
