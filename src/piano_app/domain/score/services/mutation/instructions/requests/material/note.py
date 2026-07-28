from dataclasses import dataclass

from piano_app.domain.score.models.material.primitive import Note
from piano_app.domain.score.models.notation import (
    Accidental,
    DottedRhythmicValue,
    Fingering,
)
from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    Voice,
)
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    CreateMutationRequest,
    DeleteMutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateNoteRequest(CreateMutationRequest[Note]):
    """A request to create a note in a voice, on a staff, at a measure position."""

    voice: Voice
    staff: Staff
    measure: Measure

    position: MeasurePosition
    written_value: DottedRhythmicValue
    staff_step: int
    accidental: Accidental = Accidental.NONE
    fingering: Fingering = Fingering.NONE


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteNoteRequest(DeleteMutationRequest[Note]):
    """A request to delete a note."""
