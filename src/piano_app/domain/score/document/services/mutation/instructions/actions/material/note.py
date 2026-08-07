from dataclasses import dataclass

from piano_app.domain.score.document.models.material import Note, NoteCarrier
from piano_app.domain.score.document.models.notation import Accidental, Fingering
from piano_app.domain.score.document.models.structural import Staff
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)
from piano_app.domain.score.document.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteAction(CreateMutationAction[Note]):
    """Creates a note inside a carrier."""

    note_carrier: Bound[NoteCarrier]
    staff: Staff
    staff_step: int
    accidental: Accidental = Accidental.NONE
    fingering: Fingering = Fingering.NONE


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteNoteAction(DeleteMutationAction[Note]):
    """Deletes a note."""
