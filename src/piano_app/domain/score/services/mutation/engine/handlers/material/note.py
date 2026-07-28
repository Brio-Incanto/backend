from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.engine.handlers.base import MutationHandler
from piano_app.domain.score.services.mutation.engine.resolver import Resolver
from piano_app.domain.score.services.mutation.instructions.actions.material.note import (
    CreateNoteAction,
    DeleteNoteAction,
)


class CreateNoteHandler(MutationHandler[CreateNoteAction]):
    """Creates a note inside its carrier (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateNoteAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> Note:
        carrier: NoteCarrier = resolve(action.note_carrier)
        note: Note = Note.create(
            note_carrier=carrier,
            staff=action.staff,
            staff_step=action.staff_step,
            accidental=action.accidental,
            fingering=action.fingering,
            sink=sink,
        )
        return note


class DeleteNoteHandler(MutationHandler[DeleteNoteAction]):
    """Detaches a note from its carrier."""

    def handle(
        self,
        *,
        action: DeleteNoteAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> None:
        note: Note = action.target
        note.detach(sink=sink)
        return None
