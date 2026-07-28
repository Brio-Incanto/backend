from piano_app.domain.score.models import ScoreEntity
from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.mutation_sink import MutationSink
from piano_app.domain.score.services.mutation.instructions.actions.material.note import (
    CreateNoteAction,
)
from piano_app.domain.score.services.mutation.engine.resolver import Resolver


class CreateNoteHandler:
    """Creates a note inside its carrier (resolved from the environment)."""

    def handle(
        self,
        *,
        action: CreateNoteAction,
        resolve: Resolver,
        sink: MutationSink,
    ) -> ScoreEntity | None:
        carrier: NoteCarrier = resolve(action.note_carrier)
        note: Note = Note.create(
            note_carrier=carrier,
            staff=action.staff,
            staff_step=action.staff_step,
            pitch=action.pitch,
            fingering=action.fingering,
            sink=sink,
        )
        return note
