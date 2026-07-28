from piano_app.domain.score.models.material import Note
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.models.relations.start_end import Tie
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.relations import CreateTieAction


class CreateTieHandler(MutationHandler[CreateTieAction]):
    """Creates a tie between two notes."""

    def handle(
        self,
        *,
        action: CreateTieAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> Tie:
        start_note: Note = resolve(action.start_note)
        end_note: Note = resolve(action.end_note)
        relation: Tie = Tie.create(
            start_note=start_note,
            end_note=end_note,
            sink=sink,
        )
        return relation
