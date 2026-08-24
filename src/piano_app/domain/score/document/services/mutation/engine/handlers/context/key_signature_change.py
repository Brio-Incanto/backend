from piano_app.domain.score.document.models.context import KeySignatureChange
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.context import (
    CreateKeySignatureChangeAction,
)


class CreateKeySignatureChangeHandler:
    """Creates a key signature change on its anchor (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateKeySignatureChangeAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> KeySignatureChange:
        start: TemporalAnchor = resolve(action.start)
        return KeySignatureChange.create(
            start=start,
            staff=action.staff,
            symbols=action.symbols,
            sink=sink,
        )
