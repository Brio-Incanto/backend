from piano_app.domain.score.document.models.material import Note, NoteCarrier
from piano_app.domain.score.document.models.mutation_sink import MutationSink
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.material import (
    CreateNoteAction,
    DeleteNoteAction,
)


class CreateNoteHandler:
    """Creates a note inside its carrier (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateNoteAction,
        resolve: ResolveBound,
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


class DeleteNoteHandler:
    """Detaches a note from its carrier."""

    def handle(
        self,
        *,
        action: DeleteNoteAction,
        resolve: ResolveBound,
        sink: MutationSink,
    ) -> None:
        note: Note = action.target
        note.detach(sink=sink)
        return None
