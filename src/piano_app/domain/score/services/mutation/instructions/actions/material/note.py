from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.notation import Fingering, Pitch
from piano_app.domain.score.models.structural import Staff
from piano_app.domain.score.services.mutation.instructions.actions import CreateMutationAction
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteAction(CreateMutationAction[Note]):
    """Creates a note inside a carrier.

    The carrier may be an existing chord (passed by identity) or one produced
    earlier in the plan (passed as a ``ResultRef``). The created note is
    published through ``out``.
    """

    note_carrier: Bound[NoteCarrier]
    staff: Staff
    staff_step: int
    pitch: Pitch
    fingering: Fingering = Fingering.NONE
